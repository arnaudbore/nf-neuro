import argparse
from pathlib import Path
import yaml
import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape

from docs.astro.formatting import (
    format_choices,
    format_description,
    link,
    sanitize_html_outside_codeblocks,
)


DOC_URL_BASE = "https://nf-neuro.github.io"


def channel_description_format(description):
    """Format channel descriptions for subworkflow tables.

    Splits on ``Structure:`` lines to format the structure separately,
    then sanitises the result for safe MDX rendering.
    """
    _descr = description.split("\n")
    try:
        _structure = next(filter(lambda x: "Structure:" in x, _descr))
    except StopIteration:
        return sanitize_html_outside_codeblocks(
            " ".join(_descr), table_cell=True
        )

    _descr.remove(_structure)
    _structure = _structure.replace('[', '`[', 1)[::-1].replace(']', ']`', 1)[::-1]
    return "{}<br />{}".format(
        format_description('\n'.join(_descr)),
        sanitize_html_outside_codeblocks(_structure, table_cell=True)
    )


def component_format(component):
    ctype = "module" if "/" in component else "subworkflow"
    return f"[{component}]({DOC_URL_BASE}/api/{ctype}s/{component})"


def _create_parser():
    p = argparse.ArgumentParser(
            description='Generate subworkflow markdown from template',
            formatter_class=argparse.RawTextHelpFormatter)

    p.add_argument('subworkflow_path', help='Name of the subworkflow')
    p.add_argument('current_commit_sha', help='Current commit sha')
    p.add_argument('output', help='Name of the output markdown file')

    return p


def main():
    parser = _create_parser()
    args = parser.parse_args()

    _templates_dir = Path(__file__).resolve().parent / 'templates'
    env = Environment(
        loader=FileSystemLoader(_templates_dir),
        autoescape=select_autoescape()
    )
    env.filters.update({
        'component_format': component_format,
        'link_tool': link,
        'channel_descr': channel_description_format,
        'format_choices': format_choices,
        'format_description': format_description
    })

    with open(f"{args.subworkflow_path}/meta.yml", "r") as f:
        data = yaml.safe_load(f)

    data["currentcommit"] = args.current_commit_sha
    data["currentdate"] = datetime.datetime.now().strftime("%Y-%m-%d")

    template = env.get_template('subworkflow.md.jinja2')
    output_path = Path(args.output)
    output_path.write_text(template.render(**data))


if __name__ == "__main__":
    main()
