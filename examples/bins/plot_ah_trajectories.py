#!/usr/bin/env python3

# Copyright (C) 2020-2021 Gabriele Bozzola
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <https://www.gnu.org/licenses/>.

import logging
import os

import matplotlib.pyplot as plt
import numpy as np

from kuibit.simdir import SimDir
from kuibit import argparse_helper as pah
from kuibit.visualize_matplotlib import (
    setup_matplotlib,
    add_text_to_figure_corner,
    save,
)

"""This script plots the trajectories of given apparent horizons. """

if __name__ == "__main__":
    setup_matplotlib()

    desc = """Plot trajectories of given apparent horizons."""

    parser = pah.init_argparse(desc)
    pah.add_figure_to_parser(parser)

    parser.add_argument(
        "-t",
        "--type",
        type=str,
        choices=["3D", "xy", "xz", "yz"],
        default="3D",
        help="Type of plot: 3D, or of a specific plane (default: %(default)s).",
    )

    parser.add_argument(
        "-a",
        "--horizons",
        type=int,
        required=True,
        help="Apparent horizons to plot",
        nargs="+",
    )

    parser.add_argument(
        "--draw-horizons",
        help="Draw the apparent horizons, if available",
        action="store_true",
    )
    args = pah.get_args(parser)

    # Parse arguments

    logger = logging.getLogger(__name__)

    if args.verbose:
        logging.basicConfig(format="%(asctime)s - %(message)s")
        logger.setLevel(logging.DEBUG)

    if args.figname is None:
        horizons = "_".join([str(h) for h in args.horizons])
        figname = f"ah_{horizons}_trajectory_{args.type}"
    else:
        figname = args.figname

    logger.debug(f"Figname: {figname}")

    sim = SimDir(args.datadir)
    sim_hor = sim.horizons

    logger.debug(
        f"Apparent horizons available: {sim_hor.available_apparent_horizons}"
    )

    # Check that the horizons are available
    for ah in args.horizons:
        if ah not in sim_hor.available_apparent_horizons:
            raise ValueError(f"Apparent horizons {ah} is not available")

    # Now we prepare the dictionaries with the centroids. The keys are
    # the horizon numbers and the values are timeseries
    x_coord = {}
    y_coord = {}
    z_coord = {}

    horizons = {}

    for ah in args.horizons:
        logger.debug(f"Reading horizon {ah}")
        # We can use any index for the qlm index, it will be thrown away
        horizons[ah] = sim_hor[0, ah]
        x_coord[ah] = horizons[ah].ah.centroid_x
        y_coord[ah] = horizons[ah].ah.centroid_y
        z_coord[ah] = horizons[ah].ah.centroid_z

    # Plot
    fig = plt.figure()

    if args.type == "3D":
        logger.debug("Plotting 3D")
        from mpl_toolkits.mplot3d import Axes3D

        ax = fig.gca(projection="3d")

        # We keep track of all the data just to set the axes ratio to equal
        # https://stackoverflow.com/a/21765085
        X = np.array([])
        Y = np.array([])
        Z = np.array([])

        for ah in args.horizons:
            ax.plot(
                x_coord[ah].y,
                y_coord[ah].y,
                z_coord[ah].y,
                label=f"Horizon {ah}",
            )

            X = np.append(X, x_coord[ah].y)
            Y = np.append(Y, y_coord[ah].y)
            Z = np.append(Z, z_coord[ah].y)

            time = x_coord[ah].tmax

            # Try to draw the shape of the horizon
            if args.draw_horizons and time in horizons[ah].shape_times:
                logger.debug(f"Drawing shape at time {time} for ah {ah}")
                shape_xyz = [
                    np.concatenate(
                        [
                            patch
                            for patch in horizons[ah].shape_at_time(time)[dim]
                        ]
                    )
                    for dim in range(3)
                ]
                # This is not the correct way to do this, but it is acceptable for the moment
                ax.plot_surface(*shape_xyz)

                X = np.append(X, shape_xyz[0])
                Y = np.append(Y, shape_xyz[1])
                Z = np.append(Z, shape_xyz[2])
            else:
                logger.debug(f"Shape not available at {time} for ah {ah}")

        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("z")

        max_range = (
            np.array(
                [X.max() - X.min(), Y.max() - Y.min(), Z.max() - Z.min()]
            ).max()
            / 2.0
        )

        mid_x = (X.max() + X.min()) * 0.5
        mid_y = (Y.max() + Y.min()) * 0.5
        mid_z = (Z.max() + Z.min()) * 0.5
        ax.set_xlim(mid_x - max_range, mid_x + max_range)
        ax.set_ylim(mid_y - max_range, mid_y + max_range)
        ax.set_zlim(mid_z - max_range, mid_z + max_range)

    else:
        logger.debug("Plotting 2D")
        coords = {"x": x_coord, "y": y_coord, "z": z_coord}
        to_plot_x, to_plot_y = args.type
        logger.debug(f"Plotting on the x axis {to_plot_x}")
        logger.debug(f"Plotting on the y axis {to_plot_y}")

        ax = fig.gca()

        for ah in args.horizons:
            ax.plot(
                coords[to_plot_x][ah].y,
                coords[to_plot_y][ah].y,
                label=f"Horizon {ah}",
            )

            time = x_coord[ah].tmax

            # Try to draw the shape of the horizon
            if args.draw_horizons and time in horizons[ah].shape_times:

                cut = {
                    "xy": (None, None, 0),
                    "xz": (None, 0, None),
                    "yz": (0, None, None),
                }

                logger.debug(f"Drawing shape at time {time} for ah {ah}")
                shape = horizons[ah].shape_outline_at_time(
                    time, cut[args.type]
                )
                ax.fill(shape[0], shape[1])
            else:
                logger.debug(f"Shape not available at {time} for ah {ah}")

        ax.set_xlabel(to_plot_x)
        ax.set_ylabel(to_plot_y)

        ax.set_aspect("equal")

    ax.legend()
    time = x_coord[ah].tmax
    add_text_to_figure_corner(fr"$t = {time:.3f}$")

    output_path = os.path.join(args.outdir, figname)
    logger.debug(f"Saving in {output_path}")
    plt.tight_layout()
    save(output_path, args.fig_extension, as_tikz=args.as_tikz)
