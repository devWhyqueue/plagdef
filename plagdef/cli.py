"""Console script for PlagDef."""
import sys

import click

from plagdef.model import detect_matches, Report


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument('docdir', type=click.Path(exists=True))
@click.option('--outdir', '-o', type=click.Path(), default='out', help='Output directory for XML reports.')
def main(docdir: click.Path, outdir: click.Path):
    """
    \b
    PlagDef supports plagiarism detection for student assignments.
    It must be provided a directory DOCDIR containing documents to be examined.
    """
    for p in sys.path:
        print(p)
    matches = detect_matches(docdir)
    report = Report(matches, outdir)
    click.echo(report.text())
    # TODO: Add XML option
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
