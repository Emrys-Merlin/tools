#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer>=0.27.2",
#     "loguru",
# ]
# ///

import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from typing import Annotated
from typer import Typer, Option
from time import sleep
from loguru import logger

main = Typer()


def check_available_gpus(verbose: bool) -> list[int]:
    try:
        output = subprocess.check_output(
            [
                "nvidia-smi",
                "-q",
                "-x",
            ],
            text=True,
        )
    except Exception as e:
        logger.info("Unable to run 'nvidia-smi'.")
        if verbose:
            logger.debug(e)
        exit(1)

    root = ET.fromstring(output)
    return [
        i
        for i, gpu in enumerate(root.findall("gpu"))
        if not gpu.findall("./processes/process_info")
    ]


def loop_body(
    command: list[str],
    n_gpus: int,
    verbose: bool,
    env_variable_name: str,
) -> None:
    free_gpus = check_available_gpus(verbose)

    if (n_free := len(free_gpus)) < n_gpus:
        logger.info(f"Not enough GPUs available: {n_free} / {n_gpus}")
        return

    logger.info(
        f"Enough GPUs available ({n_free} / {n_gpus}). "
        f'Storing list in ENV variable "{env_variable_name}". '
        f"Executing `exec`"
    )
    env = os.environ.copy()
    env[env_variable_name] = ",".join(str(i) for i in free_gpus)
    os.execvpe(command[0], command[0:], env)


@main.command()
def run(
    command: list[str],
    n_gpus: Annotated[
        int,
        Option("--n-gpus", "-n", help="The required number of free GPUs."),
    ] = 1,
    sleep_min: Annotated[
        float,
        Option(
            "--sleep",
            "-s",
            help="Sleep interval between pools in min.",
        ),
    ] = 5.0,
    env_variable_name: Annotated[
        str,
        Option(
            help="The name of the environmental variable to store the list of free GPUs"
        ),
    ] = "CUDA_VISIBLE_DEVICES",
    verbose: Annotated[
        bool,
        Option(
            "--verbose",
            "-v",
            help="Show debug output.",
        ),
    ] = False,
) -> None:
    """Poll for free GPUs before launching an executable.

    The list of free GPUs will be stored in an ENV variable (CUDA_VISIBLE_DEVICES by default)
    before launching the executable. So, the executable can pick up on which devices are free.

    Example usage:
        ```
        poll-gpus.py -n 2 -s 1 -- printenv CUDA_VISIBLE_DEVICES
        poll-gpus.py -n 2 -s 1 -- sh -c 'echo $CUDA_VISIBLE_DEVICES'
        ```

        This will poll every minute for 2 free GPUs before printing the updated ENV variable.
        The second launches an updated shell before printing if you need it.
    """
    sleep_sec = sleep_min * 60
    level = "DEBUG" if verbose else "INFO"
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format="<blue>{time} {level:>5}:</blue> {message}",
        filter="__main__",
        level=level,
    )

    logger.info(
        f"Polling every {sleep_min} min for {n_gpus} free GPU(s) before launching command."
    )
    logger.info("Interrupt with Ctrl+C.")

    while True:
        loop_body(
            command,
            n_gpus,
            verbose,
            env_variable_name,
        )
        sleep(sleep_sec)


if __name__ == "__main__":
    main()
