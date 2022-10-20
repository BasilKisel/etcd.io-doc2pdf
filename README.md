# etcd.io-doc2pdf

A simple script to scrap *.md into *.pdf for [etcd docs](https://etcd.io/docs).

All provided code was tested for Ubuntu Focal Fossa. I suggest you to use a virtual machine, wsl distro, docker container or another isolated environment. You would likely tear down the environment since it takes quite a lot of disk space.

# Prerequisites

* python3 &mdash; interpreter for the script, version 3.9.5 and above required (for Ubuntu `apt-get install python3 python3-pip`);
* git &mdash; a tool to clone the [etcd.io website](https://github.com/etcd-io/website) repository (for Ubuntu `apt-get install git`);
* pandoc &mdash; a tool to convert Markdown to intermediate HTML (for Ubuntu: `apt-get install pandoc`);
* wkhtmltopdf &mdash; a tool to convert HTML to PDF (take a package from official [website](https://wkhtmltopdf.org/downloads.html));
* pypandoc and pdfkit &mdash; a python wrapper around `pandoc` and `wkhtmltopdf` utilities (`pip install pypandoc pdfkit`);

# Usage

1. Clone this project repo, for example `git clone https://github.com/BasilKisel/etcd.io-doc2pdf.git`
2. Set `exec` right on `main.py` (for linux `chmod +x main.py`)
3. Clone the project of [etcd.io website](https://github.com/etcd-io/website), for example `git clone https://github.com/etcd-io/website.git`)
4. Launch the script using parameters:
    1. path to docs directory,
    2. path to output Markdown file.

    An example with Etcd website repo in `/tmp` directory and output file `/tmp/etcd_3.5.pdf` is
    ```
    ./main.py /tmp/website/content/en/docs/v3.5/ /tmp/etcd_3.5.pdf
    ```