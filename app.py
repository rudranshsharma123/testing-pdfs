__copyright__ = "Copyright (c) 2021 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import base64
import mimetypes
import os
from re import search
import sys
import cv2
import glob
import click
from jina import Document, Flow
from jina.logging.profile import TimeContext
from jina.types.arrays.document import DocumentArray
from jina.logging.predefined import default_logger as logger

MAX_DOCS = int(os.environ.get("JINA_MAX_DOCS", 50))
PDF_DATA_PATH = 'toy_data'


def config():
    os.environ["JINA_WORKSPACE"] = os.environ.get("JINA_WORKSPACE", "workspace")
    os.environ["JINA_PORT"] = os.environ.get("JINA_PORT", str(12345))


def index_generator(data_path):
    for path in data_path:
        doc = Document()
        with open(f"{path}", 'r') as f:
            x = f.read()
        doc.buffer = x
        # doc.mime_type = 'application/pdf'
        yield doc


def search_generator(data_path):
    d = Document()
    d.content = data_path
    yield d


def log_search_results(resp) -> None:
    search_result = ''.join([f'- {match.uri} \n' for match in resp.docs[0].matches])
    logger.info(f'The search returned the following documents \n{search_result}')


def index(num_docs: int) -> None:
    workspace = os.environ['JINA_WORKSPACE']
    if os.path.exists(workspace):
        print(f'\n +---------------------------------------------------------------------------------+ \
                        \n |                                   🤖🤖🤖                                        | \
                        \n | The directory {workspace} already exists. Please remove it before indexing again. | \
                        \n |                                   🤖🤖🤖                                        | \
                        \n +---------------------------------------------------------------------------------+')
        sys.exit(1)
    pdf_files = glob.glob(os.path.join(PDF_DATA_PATH, '*.pdf'))[: 1]
    f = Flow.load_config('flows/index.yml')
    with open(os.path.join(os.curdir, 'toy_data/blog1.pdf'), 'rb') as pdf:
        x = pdf.read()
    arr = DocumentArray()
    doc = Document()
    doc.buffer = x
    # doc.uri = os.path.join(os.curdir, 'toy_data/blog1.pdf')
    # doc.convert_uri_to_datauri()
    arr.append(doc)
    with f:
        with TimeContext(f'QPS: indexing {len(pdf_files)}', logger=f.logger):
            f.post(on= '/index' ,inputs=arr)


def query_restful():
    f = Flow.load_config('flows/query.yml')
    f.protocol = 'http'
    f.port_expose = '12345'
    f.rest_api = True
    with f:
        f.block()


def query_text():
    f = Flow().load_config('flows/query.yml')
    with f:
        # search_text = input('Please type a sentence: ')?
        arr = DocumentArray()
        search_text = "jina"
        doc = Document(content=search_text, mime_type='text/plain')
        with open("photo-1.png", 'rb') as img:
            encoded_string2 = base64.b64encode(img.read())
        encoded_string2 = cv2.imread("photo-1.png")
        # print(encoded_string2)
        doc1 = Document(content = encoded_string2, mime_type = 'image/*')
        # Document().
        arr.append(doc)
        arr.append(doc1)
        resp = f.post('/search', inputs=arr, on_done=log_search_results, return_results = True)
        print(type(resp[0].docs[0].matches[0].text))
        # print((resp[0].docs[0].matches[0].uri))
        print(len(resp))
        print(resp[0].docs[1])


@click.command()
@click.option(
    "--task",
    "-t",
    type=click.Choice(["index", "query_text", "query_restful"], case_sensitive=False),
)
@click.option("--num_docs", "-n", default=MAX_DOCS)
def main(task, num_docs):
    config()
    if task == 'index':
        index(num_docs)
    if task == 'query_text':
        query_text()
    if task == 'query_restful':
        query_restful()


if __name__ == "__main__":
    main()
