from typing import List, Dict
import csv
import dask.dataframe as dd
import re
import pandas as pd
import os


class DataLoader:
    def __init__(self, file: str):
        self.__file: str = file
        self.__headers_loaded: Dict[str, bool] = {}
        # tocheck: not used for now. No bound on number of columns !
        # self.__max_cols: int = 15
        self.__df: dd = None

    # TODO: decide what to do with columns
    def read_headers(self, columns: List[str] = []) -> List[str]:
        """
        Read headers of the input file
        If the list of columns to read is > N, returns a list with the first N,
        otw returns the same list
        :return: list of columns to read from file
        """
        # read headers
        fin = open(self.__file, 'rt')
        it = csv.reader(fin)
        headers = next(it)
        fin.close()
        return headers

    def get_columns(self, columns: List[str]) -> dd:
        """
        Load a file in memory
        :param columns:
        :return:
        """

        # cols_to_read = self.read_headers(columns)

        def header_match_patterns(header):
            return any(re.fullmatch(regex, str(header)) for regex in columns)

        if self.__df is None:
            # print(os.path.exists(self.__file))
            self.__df = dd.read_csv(self.__file, usecols=header_match_patterns, engine='c')
            self.__headers_loaded = {k: False for k in self.read_headers()}
            curr_headers = self.__df.columns.values.tolist()
            self.__headers_loaded.update({k: True for k in curr_headers})
        else:
            to_add = set(self.__headers_loaded.keys())
            curr_headers = set(self.__df.columns.values.tolist())
            to_add.difference_update(curr_headers)

            def new_header_to_add(header):
                return (header in to_add) and header_match_patterns(header)

            new_cols = dd.read_csv(self.__file, usecols=new_header_to_add, engine='c')
            self.__df = self.__df.join(new_cols)

        return self.__df
