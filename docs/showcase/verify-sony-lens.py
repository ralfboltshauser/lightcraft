#!/usr/bin/env python3
"""Local geometry check against a camera JPEG whose RAW metadata says distortion was on.

Requires Python 3.11+, ExifTool and a separate analysis venv with numpy/opencv-python-headless.
No input media is modified or uploaded. Outputs (including source names) must stay local.
Example: python verify-sony-lens.py --cli target/release/lightcraft-cli --out target/lens-check capture.ARW
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

import cv2
import numpy as np


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def metadata(path):
    return json.loads(subprocess.check_output([
        'exiftool', '-json', '-n', '-Model', '-LensModel', '-FocalLength',
        '-DistortionCorrection', '-DistortionCorrectionSetting', '-Orientation', str(path)
    ]))[0]


def camera_orientation(image, orientation):
    # Exif orientation of the RAW applies to its embedded (sensor-oriented) JPEG too.
    if orientation in (2, 5, 7):
        image = cv2.flip(image, 1)
    if orientation in (5, 6):
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    elif orientation in (7, 8):
        image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif orientation == 3:
        image = cv2.rotate(image, cv2.ROTATE_180)
    elif orientation == 4:
        image = cv2.flip(image, 0)
    return image


def measure(image, camera):
    sift = cv2.SIFT_create(nfeatures=7000)
    ka, da = sift.detectAndCompute(image, None)
    kb, db = sift.detectAndCompute(camera, None)
    if da is None or db is None:
        return {'matches': 0, 'quality': 'inconclusive'}
    matches = [a for pair in cv2.BFMatcher().knnMatch(da, db, k=2)
               if len(pair) == 2 for a, b in [pair] if a.distance < .65 * b.distance]
    if len(matches) < 10:
        return {'matches': len(matches), 'quality': 'inconclusive'}
    a = np.array([ka[m.queryIdx].pt for m in matches])
    b = np.array([kb[m.trainIdx].pt for m in matches])
    # Reject descriptor mismatches with a deliberately loose 40px gate. The fitted
    # homography is NOT applied to the points: scale, translation and distortion
    # all remain in the measured direct output residuals.
    _, mask = cv2.findHomography(a, b, cv2.RANSAC, 40)
    if mask is None:
        return {'matches': len(matches), 'quality': 'inconclusive'}
    a, b = a[mask.ravel() > 0], b[mask.ravel() > 0]
    h, w = camera.shape
    error = np.linalg.norm(a - b, axis=1)
    radius = np.linalg.norm(b - [w / 2, h / 2], axis=1) / np.hypot(w / 2, h / 2)
    edge = radius > .7
    if len(error) == 0:
        return {'matches': 0, 'quality': 'inconclusive'}
    good_coverage = len(error) >= 50 and edge.sum() >= 10 and radius.max() >= .85
    return {
        'matches': len(error), 'median': float(np.median(error)),
        'p95': float(np.percentile(error, 95)), 'maxRadius': float(radius.max()),
        'edgeMatches': int(edge.sum()),
        'centreMatches': int((radius < .3).sum()),
        'cornerMatches': {
            name: int((edge & (b[:, 0] < w / 2 if left else b[:, 0] >= w / 2)
                       & (b[:, 1] < h / 2 if top else b[:, 1] >= h / 2)).sum())
            for name, left, top in [('topLeft', True, True), ('topRight', False, True),
                                    ('bottomLeft', True, False), ('bottomRight', False, False)]
        },
        'edgeP95': float(np.percentile(error[edge], 95)) if edge.any() else None,
        'quality': 'scorable' if good_coverage else 'inconclusive',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('files', nargs='+', type=Path)
    args = parser.parse_args()
    cv2.setNumThreads(1)
    args.out.mkdir(parents=True, exist_ok=True)
    results = []
    env = dict(os.environ, LIGHTCRAFT_GPU_BACKEND='off')
    for path in args.files:
        before = sha256(path)
        meta = metadata(path)
        if meta.get('DistortionCorrectionSetting') not in (1, 2) and meta.get('DistortionCorrection') not in (1, 17):
            results.append({'sample': path.name, 'quality': 'inconclusive', 'reason': 'camera correction not known to be enabled'})
            continue
        folder = args.out / before[:16]
        folder.mkdir(exist_ok=True)
        with (folder / 'camera.jpg').open('wb') as output:
            subprocess.run(['exiftool', '-b', '-JpgFromRaw', str(path)], stdout=output, check=True)
        # Explicit on/off overrides accommodate existing sidecars. Geometry edits in
        # a sidecar should be cleared in a throwaway session before using this tool.
        for label, enabled in [('off', False), ('on', True)]:
            settings = folder / (label + '.json')
            settings.write_text(json.dumps({'optics': {'lens_profile': enabled}}))
            subprocess.run([str(args.cli.resolve()), 'render', str(path), '-o', str(folder / (label + '.png')),
                            '--size', '1600', '--settings', str(settings)], env=env, check=True,
                           stdout=subprocess.DEVNULL)
        corrected = cv2.imread(str(folder / 'on.png'), 0)
        camera = cv2.imread(str(folder / 'camera.jpg'), 0)
        if corrected is None or camera is None:
            raise RuntimeError('render or embedded JPEG could not be read')
        camera = camera_orientation(camera, meta.get('Orientation', 1))
        camera = cv2.resize(camera, (corrected.shape[1], corrected.shape[0]))
        off = cv2.imread(str(folder / 'off.png'), 0)
        row = {'sample': path.name, 'sha256': before, 'model': meta.get('Model'),
               'lens': meta.get('LensModel'), 'focal': meta.get('FocalLength'),
               'width': corrected.shape[1], 'height': corrected.shape[0],
               'off': measure(off, camera), 'on': measure(corrected, camera)}
        on = row['on']
        row['verdict'] = ('inconclusive' if on['quality'] != 'scorable' else
                          'pass' if on['median'] <= 1 and on['p95'] <= 3 and on['edgeP95'] <= 3 else 'fail')
        if sha256(path) != before:
            raise RuntimeError('input RAW changed during validation')
        results.append(row)
        print(json.dumps(row), flush=True)
        (args.out / 'results.json').write_text(json.dumps(results, indent=2))
    (args.out / 'results.json').write_text(json.dumps(results, indent=2))
    return 1 if any(r.get('verdict') == 'fail' for r in results) else 0


if __name__ == '__main__':
    raise SystemExit(main())
