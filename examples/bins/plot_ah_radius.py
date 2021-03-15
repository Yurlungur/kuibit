#!/usr/bin/env python3

# Copyright (C) 2021 Gabriele Bozzola
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

from kuibit.simdir import SimDir
from kuibit import argparse_helper as pah
from kuibit.visualize_matplotlib import (
    setup_matplotlib,
    save,
)

"""Plot the coordinate radius of an apparent horizon as a function of time. If --dx
is passed, then add a y-axis indicating the number of points that resolve the radius,
assuming that it is all covered by the given resolution."""

if __name__ == "__main__":
    setup_matplotlib()

    desc = __doc__

    parser = pah.init_argparse(desc)
    pah.add_figure_to_parser(parser)

    parser.add_argument(
        "-a",
        "--horizon",
        type=int,
        required=True,
        help="Apparent horizons to plot",
    )

    parser.add_argument(
        "--dx",
        type=float,
        help=(
            "Grid resolution where the horizon is,"
            " assuming the entire horizon has this resolution"
        ),
    )

    args = pah.get_args(parser)

    # Parse arguments

    logger = logging.getLogger(__name__)

    if args.verbose:
        logging.basicConfig(format="%(asctime)s - %(message)s")
        logger.setLevel(logging.DEBUG)

    if args.figname is None:
        ah = args.horizon
        figname = f"ah_{ah}_radius"
    else:
        figname = args.figname

    logger.debug(f"Figname: {figname}")

    sim = SimDir(args.datadir, ignore_symlinks=args.ignore_symlinks)
    sim_hor = sim.horizons

    logger.debug(
        f"Apparent horizons available: {sim_hor.available_apparent_horizons}"
    )

    # Check that the horizons are available
    if ah not in sim_hor.available_apparent_horizons:
        raise ValueError(f"Apparent horizons {ah} is not available")

    logger.debug("Reading horizons and computing radius")
    # We can use any index for the qlm index, it will be thrown away
    horizon = sim_hor[0, ah].ah

    # Plot
    plt.ylabel(f"Radius of horizon {ah}")
    plt.xlabel("Time")
    plt.plot(horizon.mean_radius / args.dx)
    plt.plot(horizon.min_radius / args.dx)
    plt.plot(horizon.max_radius / args.dx)

    if args.dx:
        logger.debug("Adding resolution y axis")
        plt.twinx()
        plt.plot(horizon.mean_radius, label="Mean radius")
        plt.plot(horizon.min_radius, label="Min radius")
        plt.plot(horizon.max_radius, label="Max radius")
        plt.ylabel("Number of points on radius")

    plt.legend()
    output_path = os.path.join(args.outdir, figname)
    logger.debug(f"Saving in {output_path}")
    plt.tight_layout()
    save(output_path, args.fig_extension, as_tikz=args.as_tikz)
