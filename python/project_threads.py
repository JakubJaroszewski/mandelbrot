from datetime import datetime
import argparse
import multiprocessing
import time
from typing import Tuple, List
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw


def mandelbrodt_pixel(x: float, y: float, steps: int):
    re_z = 0
    im_z = 0
    counter = 0

    while counter <= steps:
        counter += 1
        re_z_square = pow(re_z, 2)
        im_z_square = pow(im_z, 2)
        re_buf = re_z
        im_buf = im_z
        re_z = re_z_square - im_z_square + x
        im_z = 2 * re_buf * im_buf + y

        if re_z_square + im_z_square >= 4:
            return False
    return True


def mandelbrodt_job(xy_values, steps, procnum, return_dict):
    return_list = []
    for x, y in xy_values:
        return_list.append([x, y, int(mandelbrodt_pixel(x, y, steps))])

    # process return clause
    return_dict[procnum] = return_list


def draw_fractal(fractal_list, fname):
    def get_ranks(arr):
        unique = np.unique(arr)
        ranks = np.argsort(unique)
        return np.array([ranks[np.where(unique == element)] for element in arr]).ravel()
    fractal_list = np.array(fractal_list)
    x = get_ranks(fractal_list[:, 0])
    y = get_ranks(fractal_list[:, 1])
    color = fractal_list[:, 2]

    im = Image.new(mode='RGB', size=(len(np.unique(x)), len(np.unique(y))))
    for x, y, c in zip(x, y, color):
        if c:
            im.putpixel((x, y), (255, 255, 255))
    im.save(fname, format='png')


def get_xy_pairs(workers: int, side_size: int, xrange: Tuple[float, float], yrange: Tuple[float, float]):
    x_min, x_max = xrange
    if x_min > x_max:
        x_min, x_max = x_max, x_min
    x_step = (x_max - x_min) / side_size

    y_min, y_max = yrange
    if y_min > y_max:
        y_min, y_max = y_max, y_min
    y_step = (y_max - y_min) / side_size

    x_values = [x_min + x * x_step for x in range(side_size)]
    y_values = [y_min + y * y_step for y in range(side_size)]

    interval_len = int(side_size / num_workers)
    intervals = [i * interval_len for i in range(num_workers + 1)]

    super_pairs = []
    for i in range(workers):
        super_pairs.append([(x, y) for x in x_values[intervals[i]:intervals[i+1]] for y in y_values])
    return super_pairs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--num-workers', required=False, default=-1, type=int,
                        help='Number of workers, if set -1 all available cores will be picked')
    parser.add_argument('--xrange', nargs=2, default=[-2, 1],
                        help='Minimum and maximum x values')
    parser.add_argument('--yrange', nargs=2, default=[-1.5, 1.5],
                        help='Minimum and maximum y values')
    parser.add_argument('--side-size', default=[32, 64, 128, 256, 512, 1024, 2048, 4096, 8192],nargs='*', type=int,
                        help='Set number of pixels on each side, provide more than one if required')
    parser.add_argument('--steps', default=200, type=int,
                        help='Steps of convergence')
    parser.add_argument('--reps', default=1, type=int,
                        help='Number of repetition of each image size')
    parser.add_argument('--save-dir', default=Path('outputs'),
                        help='Directory where to save results, if none, outputs will not be saved')
    parser.add_argument('--computation-time', action='store_true',
                        help='If set computation times will be saved')
    parser.add_argument('--draw-fractals', action='store_true',
                        help='If set fractals will be drawn and saved in save directory')

    args = parser.parse_args()

    now = datetime.now()
    save_dir = Path(args.save_dir) / now.strftime("%d-%m-%Y-%H-%M-%S")
    save_dir.mkdir(parents=True, exist_ok=True)

    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    jobs = []
    xrange = (args.xrange[0], args.xrange[1])
    yrange = (args.yrange[0], args.yrange[1])
    num_workers = multiprocessing.cpu_count() if args.num_workers < 0 else args.num_workers
    print(f'Used workers: {num_workers}')
    times = []

    for side_size in args.side_size:
        for rep in range(args.reps):
            tic = time.time()
            job_pairs = get_xy_pairs(workers=num_workers, side_size=side_size,
                                     xrange=xrange, yrange=yrange)

            for i, xy_values in enumerate(job_pairs):
                p = multiprocessing.Process(target=mandelbrodt_job,
                                            args=(xy_values, args.steps, i, return_dict))
                jobs.append(p)
                p.start()

            for proc in jobs:
                proc.join()
            times.append(time.time()-tic)
            print(f'Done size {side_size}, rep {rep}')

            if args.save_dir and args.draw_fractals:
                # join jobs results
                output = []
                for job_result in return_dict.values():
                    output.extend(job_result)
                draw_fractal(output, save_dir / f'size{side_size}rep{rep}.png')

    with open(save_dir / f'computation_time_workers{num_workers}.csv', 'a') as f:
        f.write("side_size,computation_time(s)\n")
        counter = 0
        for time, side_size in zip(times, [size for size in args.side_size for _ in range(args.reps)]):
                f.write(f"{side_size},{time}\n")
