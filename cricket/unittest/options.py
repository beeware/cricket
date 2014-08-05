"""
argparse options common to discoverer, executor and model.
"""


def add_arguments(parser):
    """
    Add unittest discovery settings to the argument parser.
    """
    parser.add_argument('start', nargs='?', default='.',
        help="Directory to start discovery ('.' default)")
    parser.add_argument('pattern', nargs='?', default='test*.py',
        help="Pattern to match tests ('test*.py' default)")
    parser.add_argument('top', nargs='?', default=None,
        help='Top level directory of project (defaults to start directory)')
