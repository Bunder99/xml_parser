import pytest
from xml_parser import CustomHandler, get_summary, main
import datetime
from argparse import Namespace
import os

expected_result = {datetime.date(2011, 12, 21): {'i.ivanov': datetime.timedelta(seconds=31695),
                                                    'a.stepanova': datetime.timedelta(seconds=3644),
                                                    'v.petrov': datetime.timedelta(seconds=10844)},
                      datetime.date(2011, 12, 22): {'a.stepanova': datetime.timedelta(seconds=24010),
                                                    'v.petrov': datetime.timedelta(days=1)},
                      datetime.date(2011, 12, 23): {'v.lomachenkoivanov': datetime.timedelta(seconds=35624),
                                                    'v.petrov': datetime.timedelta(days=1)},
                      datetime.date(2011, 12, 24): {'v.petrov': datetime.timedelta(days=1)},
                      datetime.date(2011, 12, 25): {'v.petrov': datetime.timedelta(seconds=34810)}}


def test_CustomHandler():
    assert CustomHandler().parse('test.xml') == expected_result


def test_get_summary(capsys):
    get_summary(
        expected_result,
        dates=[datetime.datetime.strptime(x, '%d-%m-%Y') for x in ['21-12-2011', '22-12-2011']],
        names=['i.ivanov', 'a.stepanova'])
    assert capsys.readouterr().out == 'date: 2011-12-21, total_time: 9:48:59\n' \
                                    '     i.ivanov: 8:48:15\n' \
                                    '     a.stepanova: 1:00:44\n' \
                                    '--------------------------------------------------\n' \
                                    'date: 2011-12-22, total_time: 6:40:10\n' \
                                    '     i.ivanov: 0:00:00\n' \
                                    '     a.stepanova: 6:40:10\n' \
                                    '--------------------------------------------------\n'


@pytest.fixture
def get_args():
    def _args(path, date=None, name=None, search=False):
        args = Namespace()
        args.Path = path
        args.date = date
        args.name = name
        args.search = search
        return args
    return _args


def test_main(capsys, get_args):
    args = get_args('test1234.xml')
    with pytest.raises(SystemExit):
        main(args)
    assert capsys.readouterr().out == '\n*** ERROR: XML file not found, please check path ***\n'

    args = get_args('test.xml', date=['12-12-12'])
    with pytest.raises(SystemExit) as exc:
        main(args)
    assert exc.value.code == 2

    args = get_args('test.xml', date=['12-12-2012', '15-12-2012', '18-12-2012'])
    with pytest.raises(SystemExit) as exc:
        main(args)
    assert exc.value.code == 3

    args = get_args('test.xml', date=['12-12-2012', '15-12-2012'], name=['ivan.ivanov'])
    with pytest.raises(SystemExit) as exc:
        main(args)
    assert exc.value.code == 4

    args = get_args('test.xml')
    main(args)
    assert os.path.exists((os.path.join(os.path.dirname(os.path.abspath(__file__)),
			'data',
			os.path.basename(args.Path).replace('.xml', '.pkl')))) == True