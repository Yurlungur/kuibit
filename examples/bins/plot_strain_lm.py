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

from kuibit.simdir import SimDir
from kuibit import argparse_helper as pah
from kuibit.visualize_matplotlib import (
    setup_matplotlib,
    save,
)


"""Plot the (l,m) gravitational-wave strain.

Optionally, a window function can be applied to the data before performing the
integration. To do this, use the --window flag passing the name of a method
defined in TimeSeries (e.g. 'tukey'). Then, pass all the arguments with
--window-args in the order as they appear in the TimeSeries method."""

if __name__ == "__main__":
    setup_matplotlib()

    desc = __doc__

    parser = pah.init_argparse(desc)
    pah.add_figure_to_parser(parser)

    parser.add_argument(
        "--detector-num",
        type=int,
        required=True,
        help="Number of the spherical surface over which to read Psi4",
    )

    parser.add_argument(
        "--pcut",
        type=float,
        required=True,
        help="Period for the fixed frequency integration",
    )

    parser.add_argument(
        "--mult-l", type=int, default=2, help="Multipole number l"
    )
    parser.add_argument(
        "--mult-m", type=int, default=2, help="Multipole number m"
    )

    parser.add_argument(
        "--window",
        help="Window function to apply before performing the integration",
    )

    parser.add_argument(
        "--window-args",
        nargs="*",
        type=float,
        help="Arguments of the window function",
    )

    args = pah.get_args(parser)

    # Parse arguments

    if args.figname is None:
        figname = f"strain_{args.mult_l}{args.mult_m}_det{args.detector_num}"
    else:
        figname = args.figname

    logger = logging.getLogger(__name__)

    if args.verbose:
        logging.basicConfig(format="%(asctime)s - %(message)s")
        logger.setLevel(logging.DEBUG)

    sim = SimDir(args.datadir, ignore_symlinks=args.ignore_symlinks)
    reader = sim.gravitationalwaves

    radius = reader.radii[args.detector_num]
    detector = reader[radius]

    if (args.mult_l, args.mult_m) not in detector.available_lm:
        logger.debug(f"Available multipoles {detector.available_lm}")
        raise ValueError(
            f"Multipole {args.mult_l}, {args.mult_m} not available"
        )

    logger.debug("Computing strain")

    strain = detector.get_strain_lm(
        args.mult_l,
        args.mult_m,
        args.pcut,
        *args.window_args,
        window_function=args.window,
    )

    plt.plot(
        strain.real(),
        label=fr"$r_{{\mathrm{{ex}}}} h^{{{args.mult_l}{args.mult_m}}}_+$",
    )
    plt.plot(
        -strain.imag(),
        label=fr"$r_{{\mathrm{{ex}}}} h^{{{args.mult_l}{args.mult_m}}}_\times$",
    )

    plt.legend()
    plt.xlabel("Time")
    plt.ylabel(fr"$r_{{\mathrm{{ex}}}} h^{{{args.mult_l}{args.mult_l}}}$")

    output_path = os.path.join(args.outdir, figname)
    logger.debug(f"Saving in {output_path}")
    plt.tight_layout()
    save(output_path, args.fig_extension, as_tikz=args.as_tikz)
