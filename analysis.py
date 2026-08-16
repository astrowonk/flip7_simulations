import polars as pl


def rate_error(col, col_count):
    return 1.96 * (pl.col(col) * (1 - pl.col(col)) / pl.col(col_count)).sqrt()


def pipe_rate_error(_df: pl.LazyFrame | pl.DataFrame, col, col_count):
    return _df.with_columns(rate_error(col, col_count).alias(f'{col}_error'))


def make_df(out):
    """output to polars dataframe"""
    return (
        pl
        .DataFrame(out)
        .with_columns(rank=pl.col('score').rank(descending=True).over('game'))
        .with_columns(
            winner=pl.col('score').eq(pl.col('score').max().over(pl.col('game'))),
        )
    )


def table_from_out(out):
    return (
        make_df(out)
        .group_by('name')
        .agg(
            pl.col('winner').mean(),
            pl.col('rank').mean(),
            pl.col('rank').mode().first().alias('rank_mode'),
            # pl.col('winner').std().alias('std_winner'),
            pl.col('score').mean(),
            pl.col('score').std().alias('std_score'),
            pl.col('busted').sum(),
            pl.col('rounds').sum(),
            pl.col('game').count().alias('count'),
        )
        .sort('winner', descending=True)
        .pipe(pipe_rate_error, 'winner', 'count')
        .with_columns(bust_pct=pl.col('busted') / 'rounds')
        .style.fmt_percent([
            'bust_pct',
            'winner',
            'winner_error',
        ])
        .fmt_number(['score', 'std_score'])
    )
