"""Console script for PlagDef."""
import pathlib
import sys

import click
import pkg_resources
from click import UsageError

from plagdef.model.detection import find_matches
from plagdef.model.legacy.algorithm import InvalidConfigError
from plagdef.model.preprocessing import UnsupportedLanguageError, DocumentFactory
from plagdef.model.reporting import generate_xml_reports, generate_text_report
from plagdef.repositories import DocumentFileRepository, UnsupportedFileFormatError, DocumentPairReportFileRepository, \
    ConfigFileRepository, NoDocumentFilePairFoundError

CONFIG_PATH = 'config/alg.ini'


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument('docdir', type=click.Path(exists=True))
@click.option('lang', '--lang', '-l', required=True, help='Bibliographical language code of the documents\' language.')
@click.option('xmldir', '--xml', '-x', type=click.Path(), help='Output directory for XML reports.')
def main(docdir: click.Path, lang: str, xmldir: click.Path) -> int:
    """
    \b
    PlagDef supports plagiarism detection for student assignments.
    It must be provided with a directory <DOCDIR> containing at least two documents and their language.
    """
    try:
        config_path = pkg_resources.resource_filename(__name__, CONFIG_PATH)
        config_repo = ConfigFileRepository(pathlib.Path(config_path))
        config = config_repo.get()
        doc_factory = DocumentFactory(lang, config['min_sent_len'], config['rem_stop_words'])
        doc_repo = DocumentFileRepository(pathlib.Path(str(docdir)), doc_factory)
        matches = find_matches(doc_repo, config_repo)
        click.echo(f'Found {len(matches) if len(matches) else "no"} suspicious document pair'
                   f'{"s" if len(matches) > 1 else ""}.\n')
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
            FileNotFoundError, InvalidConfigError, UnsupportedLanguageError) as e:
        raise UsageError(str(e)) from e


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
