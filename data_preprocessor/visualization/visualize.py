import dask
import dask.dataframe as dd
import matplotlib.pyplot as plt


def cat_histogram(df: dask.dataframe, col: str):
    # df_array_series = df[col].to_dask_array(lengths=True)
    hist_series = df[col].value_counts().to_dask_array(lengths=True)
    plt.hist(hist_series, density=False)
    plt.show()


def num_histogram(df: dask.dataframe, col: str, bins: int):
    hist_series = df[col].to_dask_array(lengths=True)
    plt.hist(hist_series, bins=bins, density=False)