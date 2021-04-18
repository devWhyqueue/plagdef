import signal
import sys

import click

from plagdef import bootstrap
from plagdef.model.reporting import generate_text_report

# Core functions of PlagDef
find_matches = bootstrap.find_matches()
write_xml_reports = bootstrap.write_xml_reports()


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument('docdir', type=click.Path(exists=True))
@click.option('lang', '--lang', '-l', required=True, help='Bibliographical language code of the documents\' language.')
@click.option('rec', '--recursive', '-R', is_flag=True,
              help='Recursively search for documents in subdirectories.')
@click.option('common_docdir', '--common-docs', '-c', type=click.Path(exists=True),
              help='Directory containing documents with sentences which should be excluded from detection.')
@click.option('xmldir', '--xml', '-x', type=click.Path(), help='Output directory for XML reports.')
def cli(docdir: click.Path, lang: str, common_docdir: click.Path, xmldir: click.Path, rec: bool):
    """
    \b
    PlagDef supports plagiarism detection for student assignments.
    It must be provided with a directory <DOCDIR> containing at least two documents and their language.
    """
    matches = find_matches(lang, docdir, recursive=rec, common_doc_dir=common_docdir)
    click.echo(f'Found {len(matches) if len(matches) else "no"} suspicious document pair'
               f'{"s" if len(matches) > 1 else ""}.\n')
    if matches:
        if xmldir:
            write_xml_reports(matches, xmldir)
            click.echo(f'Successfully wrote XML reports to {xmldir}.')
        else:
            text_report = generate_text_report(matches)
            click.echo(text_report)
    sys.exit(0)


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
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


if __name__ == "__main__":
    args = sys.argv
    if len(args) > 1 and args[1] == 'gui':
        del args[1]
        gui()
    else:
        cli()
