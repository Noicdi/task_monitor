from task_monitor.cli import build_parser


def test_cli_requires_config_and_job():
    args = build_parser().parse_args(["--config", "config.toml", "--job", "daily"])

    assert args.config == "config.toml"
    assert args.job == "daily"

