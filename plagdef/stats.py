from pathlib import Path
from pickle import load

import click


@click.command()
@click.argument('file', type=click.Path(exists=True))
def count(file):
    with Path(file).open('rb') as f:
        docs = load(f)
    word_count = 0
    for doc in docs:
        for sent in doc._sents:
            word_count += len(sent.words)
    word_count /= len(docs)
    click.echo(f'Average word count in {len(docs)} documents is {word_count} words.')


if __name__ == "__main__":
    count()
