"""Console script for PlagDef."""
import pathlib
import sys

import click
from click import UsageError

from plagdef.algorithm import InvalidConfigError
from plagdef.model import find_matches, generate_text_report, generate_xml_reports
from plagdef.repositories import DocumentFileRepository, UnsupportedFileFormatError, DocumentPairReportFileRepository, \
    ConfigFileRepository, NoDocumentFilePairFoundError


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument('docdir', type=click.Path(exists=True))
@click.option('xmldir', '--xml', '-x', type=click.Path(), help='Output directory for XML reports.')
def main(docdir: click.Path, xmldir: click.Path) -> int:
    """
    \b
    PlagDef supports plagiarism detection for student assignments.
    It must be provided a directory <DOCDIR> containing at least two documents.
    """
    try:
        doc_repo = DocumentFileRepository(pathlib.Path(str(docdir)))
        config_repo = ConfigFileRepository(pathlib.Path('settings.ini'))
        matches = find_matches(doc_repo, config_repo)
        click.echo(f'Found {len(matches) if len(matches) else "no"} suspicious document pair'
                   f'{"s" if len(matches) > 1 else ""}.')
        if matches:
            if xmldir:
                doc_pair_report_repo = DocumentPairReportFileRepository(pathlib.Path(str(xmldir)))
                generate_xml_reports(matches, doc_pair_report_repo)
                click.echo(f'Successfully wrote XML reports to {xmldir}.')
            else:
                text_report = generate_text_report(matches)
                click.echo(text_report)
        return 0
    except (NotADirectoryError, NoDocumentFilePairFoundError, UnsupportedFileFormatError,
            FileNotFoundError, InvalidConfigError) as e:
        raise UsageError(str(e)) from e


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
