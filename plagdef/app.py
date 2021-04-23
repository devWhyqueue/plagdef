from __future__ import annotations

import logging.config
import signal
import sys
from pathlib import Path

import click
import pkg_resources
from click import UsageError

from plagdef import services
from plagdef.gui.model import DocumentPairMatches
from plagdef.model.reporting import generate_text_report
from plagdef.repositories import ConfigFileRepository, DocumentFileRepository, NoDocumentFilePairFoundError, \
    DocumentPairReportFileRepository

# Load configs
LOGGING_CONFIG = pkg_resources.resource_filename(__name__, str(Path('config/logging.ini')))
ALG_CONFIG_PATH = pkg_resources.resource_filename(__name__, str(Path('config/alg.ini')))
logging.config.fileConfig(LOGGING_CONFIG, disable_existing_loggers=False)
config_repo = ConfigFileRepository(Path(ALG_CONFIG_PATH))


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(prog_name='PlagDef', package_name='plagdef')
@click.argument('docdir', type=(click.Path(exists=True), bool))
@click.option('lang', '--lang', '-l', required=True, help='Bibliographical language code of the documents\' language.')
@click.option('archive_docdir', '--archive-docs', '-a', type=(click.Path(exists=True), bool),
              help='Directory containing older documents which should not be compared among themselves but only with '
                   'the documents in <DOCDIR>.')
@click.option('common_docdir', '--common-docs', '-c', type=(click.Path(exists=True), bool),
              help='Directory containing documents with sentences which should be excluded from detection.')
@click.option('xmldir', '--xml', '-x', type=click.Path(), help='Output directory for XML reports.')
def cli(docdir: tuple[click.Path, bool], lang: str, common_docdir: [click.Path, bool],
        archive_docdir: [click.Path, bool], xmldir: click.Path):
    """
    \b
    PlagDef supports plagiarism detection for student assignments.
    It must be provided a <DOCDIR> <RECURSIVE> tuple and the language option.
    The chosen directory must contain at least two documents.
    For instance if you would like to recursively search <DOCDIR> the correct command looks like this:
    `plagdef <DOCDIR> True`
    """
    archive_doc_dir = (str(archive_docdir[0]), archive_docdir[1]) if archive_docdir else None
    common_doc_dir = (str(common_docdir[0]), common_docdir[1]) if common_docdir else None
    matches = find_matches(lang, (str(docdir[0]), docdir[1]), archive_doc_dir, common_doc_dir)
    click.echo(f'Found {len(matches) if len(matches) else "no"} suspicious document pair'
               f'{"s" if len(matches) > 1 else ""}.\n')
    if matches:
        if xmldir:
            try:
                doc_pair_report_repo = DocumentPairReportFileRepository(Path(str(xmldir)))
                services.write_xml_reports(matches, doc_pair_report_repo)
                click.echo(f'Successfully wrote XML reports to {xmldir}.')
            except NotADirectoryError as e:
                raise UsageError(str(e)) from e
        else:
            text_report = generate_text_report(matches)
            click.echo(text_report)
    sys.exit(0)


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(prog_name='PlagDef', package_name='plagdef')
def gui():
    """
    \b
    PlagDef supports plagiarism detection for student assignments.
    The GUI for this tool is based on the Qt 6 framework and works on all platforms.
    """
    from plagdef.gui.main import MyQtApp
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = MyQtApp(find_matches)
    app.window.show()
    sys.exit(app.exec_())


def find_matches(lang: str, docdir: tuple[str, bool], archive_docdir: [str, bool], common_docdir: [str, bool]) \
    -> list[DocumentPairMatches]:
    try:
        doc_repo = DocumentFileRepository(Path(str(docdir[0])), lang, docdir[1])
        archive_repo = common_repo = None
        if archive_docdir:
            archive_repo = DocumentFileRepository(
                Path(str(archive_docdir[0])), lang, at_least_two=False, recursive=archive_docdir[1])
        if common_docdir:
            common_repo = DocumentFileRepository(
                Path(str(common_docdir[0])), lang, at_least_two=False, recursive=common_docdir[1])
        return services.find_matches(doc_repo, config_repo, archive_repo=archive_repo, common_doc_repo=common_repo)
    except (NotADirectoryError, NoDocumentFilePairFoundError) as e:
        raise UsageError(str(e)) from e


if __name__ == "__main__":
    args = sys.argv
    if len(args) > 1 and args[1] == 'gui':
        del args[1]
        gui()
    else:
        cli()
