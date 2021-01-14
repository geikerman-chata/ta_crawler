import os
from bs4 import BeautifulSoup
import gzip
import linecache
import re

class FileError(Exception):
    pass

class InputError(Exception):
    pass

class SpiderFeeder():
    def __init__(self, filenumber, start_idx=0, unzip=False):
        self.path = os.path.join(os.getcwd(), 'input')
        self.zip_files = [file for file in os.listdir(self.path) if '.gz' in file]
        self.unzip = unzip
        self.url_list = []
        self.current_url = None
        self.start_index = start_idx
        self.continue_feed = True

        if self.zip_files:
            self.current_file = self.zip_files[filenumber]
            self.url_txt_file_name = self.current_file.replace('.xml.gz', '_url.txt')
        else:
            raise FileError(
                'No zip files in folder, run download_hotel_xml.py to populate input folder with zip files to open'
                            )
        self.zipfile_id = self.current_file.split('-')[-1].replace('.xml.gz', '')
        self.marker_file_name = self.current_file.replace('.xml.gz', '_marker_{}.txt'.format(self.start_index))

        if not self.does_file_exist(self.marker_file_name):
            self.marker = self.start_index
            self.update_marker_file(self.marker)

        else:
            self.marker = self.read_marker_file()

        if not self.does_file_exist(self.url_txt_file_name) or unzip:
            print('Unzipping URL list: {}'.format(self.current_file))
            self.url_list = self.unzip_url()
            self.url_list_len = len(self.url_list)
            if not self.marker >= self.url_list_len:
                self.current_url = self.url_list[self.marker]
                self.dump_url_list()
                del self.url_list
            else:
                raise InputError('Start index {} must be less than the length of url list {}'.format(self.marker,
                                                                                                     self.url_list_len))
        else:
            self.current_url = self.read_url_at_marker()
            self.url_list_len = self.read_num_lines(self.url_txt_file_name)

    def does_file_exist(self, file):
        return os.path.isfile(os.path.join(self.path, file))

    def find_stop_index(self):
        folder_contents = os.listdir(self.path)
        marker_list = [marker for marker in folder_contents if str(self.zipfile_id) + '_marker_' in marker]
        stop_idx_candidates = []
        for marker_idx in marker_list:
            regex = '(?<=_marker_).*?(?=.txt)'
            stop_idx_candidate = re.search(regex, marker_idx)
            if stop_idx_candidate:
                stop_idx_candidates.append(int(stop_idx_candidate.group(0)))
        return self.find_closest_in_list(stop_idx_candidates, self.marker)

    def find_closest_in_list(self, num_list, target):
        nearest = min(num_list, key=lambda x: abs(x - target) if x > target else self.url_list_len-1)
        if nearest == 0:
            return self.url_list_len - 1
        else:
            return nearest - 1

    def unzip_url(self):
        with gzip.open(os.path.join(self.path, self.current_file)) as readfile:
            contents = readfile.read()
        xml_soup = BeautifulSoup(contents, "html.parser")
        return [tagged.text for tagged in xml_soup.find_all('loc')]

    def update_marker_file(self, index):
        with open(os.path.join(self.path, self.marker_file_name), 'w') as writer:
            writer.write(str(index))

    def read_marker_file(self):
        with open(os.path.join(self.path, self.marker_file_name), 'r') as reader:
            return int(reader.read())

    def dump_url_list(self):
        with open(os.path.join(self.path, self.url_txt_file_name), 'w') as writer:
            for row in self.url_list:
                writer.write(str(row) + '\n')

    def read_num_lines(self, file):
        return sum(1 for line in open(os.path.join(self.path, file)))

    def read_url_at_marker(self):
        return linecache.getline(os.path.join(self.path, self.url_txt_file_name), self.marker + 1)

    def read_file_at_line(self, file, line):
        return linecache.getline(os.path.join(self.path, file), line + 1)

    def next_url(self):
        stop_index = self.find_stop_index()
        if self.marker == self.url_list_len - 1 or self.marker >= stop_index:
            self.continue_feed = False
            self.current_url = None
        else:
            self.marker += 1
            marker = self.marker
            self.update_marker_file(marker)
            self.current_url = self.read_url_at_marker()

