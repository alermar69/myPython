
import os
import shutil

import dbf
import pandas as pd
from bs4 import BeautifulSoup
from dbfread import DBF
import numpy as np


class ProjectBases:

    def __init__(self, path_project):
        self.path_project = path_project
        self.base_equip = BaseProject(os.path.join(self.path_project, 'equip.DBF'))
        self.base_eqtype = BaseProject(os.path.join(self.path_project, 'eqtype.DBF'))
        self.base_io = BaseProject(os.path.join(self.path_project, 'units.DBF'))
        self.base_tag = BaseProject(os.path.join(self.path_project, 'variable.DBF'))

    def get_dbf(self, name_file):
        db = None
        with dbf.Table(os.path.join(self.path_project, name_file + '.DBF'), codepage='cp1251') as tb:
            db = tb.open(mode=dbf.READ_ONLY)
        return db

    def dataframe(self, name_file):
        return pd.DataFrame(DBF(os.path.join(self.path_project, name_file + '.DBF'), encoding='cp1251'))


class BaseProject:

    def __init__(self, file_name):
        self.filename = file_name

    def get_dbf(self):
        db = None
        with dbf.Table(self.filename, codepage='cp1251') as tb:
            db = tb.open(mode=dbf.READ_ONLY)
        return db

    def to_dbf(self, params_list):
        with dbf.Table(self.filename, codepage='cp1251') as tb:
            tb.open(mode=dbf.READ_WRITE)
            for params in params_list:
                tb.append(params)

    def clear_dbf(self):
        with dbf.Table(self.filename, codepage='cp1251') as tb:
            tb.open(mode=dbf.READ_WRITE)
            tb.zap()

    def dataframe(self):
        return pd.DataFrame(DBF(self.filename, encoding='cp1251'))


class Project:
    def __init__(self, name_project, name_cluster='Cluster1', name_server='IOServer1'):
        self.path_projects = r"c:\ProgramData\AVEVA\Citect SCADA 2018 R2\User"
        self.name_projects = name_project
        self.path_project = os.path.join(self.path_projects, self.name_projects)

        self.config_setProject_xls = self.get_path_file('setProject.xlsx')
        self.config_libDevice_xls = self.get_path_file('libDevice.xlsx')

        self.type_device_current = ''
        self.cluster = name_cluster
        self.server = name_server
        self.base = ProjectBases(self.path_project)

        self.set_df_xls('df_io', self.config_setProject_xls, 'IO')
        self.set_df_xls('df_equips', self.config_setProject_xls, 'LD')

    def set_df_xls(self, name_df, config_xls, sheet_name):
        self.__dict__[name_df] = None
        try:
            df = pd.read_excel(config_xls, sheet_name=sheet_name)
            df = df.astype(str)
            self.__dict__[name_df] = df
            return self.__dict__[name_df]
        except:
            pass

    def create_dbf_from_xls(self, ls_name_file):
        for name_file, key_col in ls_name_file:
            df = self.set_df_xls(f'df_{name_file}', self.config_setProject_xls, name_file)
            df_exist = self.base.dataframe(name_file)

            names = []
            if len(df_exist) != 0:
                names = list(df_exist[key_col].values)

            if df is not None:
                params_list = []
                columns = self.base.get_dbf(name_file).field_names

                for i in range(len(df)):
                    row = df.iloc[i]
                    values = {}
                    for column in columns:
                        val = ''
                        if column in df.columns:
                            val = str(row[column])
                            if val == 'nan':
                                val = ''
                        values[column] = val

                    if values[key_col] not in names:
                        params_list.append(values)
                        names.append(values[key_col])

                with dbf.Table(self.get_path_file(f'{name_file}.DBF'), codepage='cp1251') as tb:
                    tb.open(mode=dbf.READ_WRITE)
                    for params in params_list:
                        tb.append(params)

    def copy_libfile(self, ls_file):
        ls_file = ['libDevice.xlsx', 'setProject.xlsx']

        for name_file in ls_file:
            try:
                shutil.copy(
                    os.path.join('C:', 'libCitectScada', name_file),
                    self.path_project
                )
            except:
                pass

    def create_eqtype(self):
        self.create_dbf_from_xls([('eqtype', 'NAME')])

        template_dev = self.base.dataframe('eqtype')['TEMPLATE'].values
        template_dev
        for dev in template_dev:
            try:
                shutil.copy(
                    os.path.join('C:', 'libCitectScada', dev),
                    self.path_project
                )
            except:
                pass

    def create_io(self):

        if self.df_io is not None:

            # self.df_io['port'] = 'PORT1_BOARD1'
            addr = ''

            params_list = []

            df_tmp = self.base.base_io.dataframe()
            try:
                numb = int(df_tmp.iloc[-1]['NUMBER'])
            except:
                numb = 0

            df_io_exist = self.base.base_io.dataframe()

            names = []
            if len(df_io_exist) != 0:
                names = list(df_io_exist['NAME'].values)
            else:
                numb = 0

            for i in range(len(self.df_io)):
                io = self.df_io.iloc[i]

                if io['name'] not in names:
                    numb += 1

                if io['protocol'] == 'IEC61850N':
                    name_file_iec61850 = f"conf61850_{io['name']}.xml"
                    addr = f"[RUN]:{name_file_iec61850}"
                    self.create_config61850(name_file_iec61850)

                values = {'SERVER': self.server,
                          'NAME': io['name'],
                          'NUMBER': f'{numb}',
                          'ADDR': addr,
                          'PROTOCOL': io['protocol'],
                          'PORT': io['port'],
                          'MODE': 'Primary',
                          'LOGWRITE': '',
                          'LOGREAD': '',
                          'CACHE': '',
                          'CACHETIME': '',
                          'COMMENT': '',
                          'PROTOCOLID': '',
                          'LINKED': '',
                          'EXTERNDB': '',
                          'DRIVERID': '',
                          'CONNSTRING': '',
                          'REFRESH': '',
                          'TAGPREFIX': '',
                          'LASTUPDATE': '',
                          'REMOTE': '',
                          'REMOTEWRIT': '',
                          'TIME': '',
                          'PERIOD': '',
                          'PHONE': '',
                          'CALLERID': '',
                          'ONCONNECT': '',
                          'ONHANGUP': '',
                          'ONBROWSE': '',
                          'LIVEUPDATE': '',
                          'LASTVARMOD': '',
                          'MEMORY': str(io['memory']),
                          'PERSIST': '',
                          'TAGGEN': '',
                          'TAGGENTEMP': '',
                          'PRIORITY': '1',
                          'BGPOLL': '',
                          'BGPOLLRATE': '',
                          'PERSFREQ': '',
                          'PERSPATH': '',
                          'MINUPDATE': '',
                          'STALEPERIO': '',
                          'READONLY': '',
                          'EXCLUSIVE': ''}

                if values['NAME'] not in names:
                    params_list.append(values)
                    names.append(values['NAME'])

            self.base.base_io.to_dbf(params_list)

    def create_equip(self, isCreateTag=False):
        if self.df_equips is not None:

            # self.df_equips['io'] = self.df_io.iloc[0]['name']  #TODO

            params_list = []

            df_equip_exist = self.base.base_equip.dataframe()

            names = []
            if len(df_equip_exist) != 0:
                names = list(df_equip_exist['NAME'].values)

            for i in range(len(self.df_equips)):
                equip = self.df_equips.iloc[i]

                name_LD = f"{equip['name']}"
                if equip['number'].strip() != '': name_LD += f"_{equip['number']}"
                if equip['spec'].strip() != '': name_LD += f"_{equip['spec']}"

                name_equip = name_LD
                if equip['device'].strip() != '': name_equip += f"_{equip['device']}"

                values = {'NAME': name_equip,
                          'CLUSTER': self.cluster,
                          'TYPE': equip['device'],
                          'AREA': '',
                          'LOCATION': '',
                          'COMMENT': equip['comment'],
                          'CUSTOM1': f"{name_LD}\\",
                          # 'CUSTOM1': f"{equip['io']}\\",
                          'CUSTOM2': '',
                          'CUSTOM3': '',
                          'CUSTOM4': '',
                          'CUSTOM5': '',
                          'CUSTOM6': '',
                          'CUSTOM7': '',
                          'CUSTOM8': '',
                          'IODEVICE': equip['io'],
                          'PAGE': '',
                          'HELP': '',
                          'DEFSTATE': '',
                          'SCHEDULED': '',
                          'TAGPREFIX': f"{name_LD}/",
                          'TAGGENLINK': '',
                          'LINKED': '',
                          'EDITCODE': '',
                          'PARAM': '',
                          'COMPOSITE': '',
                          'REFERENCE': '',
                          'DEVSCHED': '',
                          'SCHEDID': '',
                          'ALIAS': '',
                          'CONTENT': '',
                          'HIDDEN': ''}

                if values['NAME'] not in names:
                    params_list.append(values)
                    names.append(values['NAME'])

                if isCreateTag:
                    sheet_name = equip['device'] + '_61850'
                    df_dev = pd.read_excel(self.config_libDevice_xls, sheet_name=sheet_name)
                    df_dev = df_dev.astype(str)
                    df_dev['io'] = equip['io']
                    df_dev['LD'] = name_LD
                    df_dev['equip'] = values['NAME']
                    self.create_tag(df_dev, type='IEC61850')

            self.base.base_equip.to_dbf(params_list)

    def create_tag(self, df, type='simple', replace=None):
        '''

        :param df:
        :param type: 'simple', 'IEC61850'
        :param replace:
        :return:
        '''
        df_tags_exist = self.base.base_tag.dataframe()

        names = []
        if len(df_tags_exist) != 0:
            names = list(df_tags_exist['NAME'].values)

        df_tags = pd.DataFrame()
        if replace and len(df_tags_exist) != 0:
            df_tags = df_tags_exist

        if replace:
            self.base.base_tag.clear_dbf()

        for i in range(len(df)):
            dev = df.iloc[i]
            values = self.create_tag_values(dev, type=type)

            if values['NAME'] not in names:
                df_tags = pd.concat([df_tags, pd.DataFrame([values])], ignore_index=True)
                names.append(values['NAME'])
            else:
                if replace:
                    df_tags.loc[df_tags['NAME'] == values['NAME'], :] = list(values.values())

        self.base.base_tag.to_dbf(df_tags.to_dict('records'))

    def create_tag_values(self, df, type='simple'):
        '''

        :param df:
        :param type: 'simple', 'IEC61850'
        :return:
        '''
        dev = df.fillna('')

        values = {}

        if type == 'simple':
            values = {'NAME': dev['name'],
                      'TYPE': dev['type'],
                      'UNIT': dev['io'],
                      'ADDR': "",
                      'RAW_ZERO': '',
                      'RAW_FULL': '',
                      'ENG_ZERO': '',
                      'ENG_FULL': '',
                      'ENG_UNITS': '',
                      'FORMAT': '',
                      'COMMENT': dev['comment'],
                      'EDITCODE': '',
                      'LINKED': '',
                      'OID': '',
                      'REF1': '',
                      'REF2': '',
                      'DEADBAND': '',
                      'CUSTOM': '',
                      'TAGGENLINK': '',
                      'CLUSTER': self.cluster,
                      'HISTORIAN': 'TRUE',
                      'EQUIP': '',
                      'CUSTOM1': '',
                      'CUSTOM2': '',
                      'CUSTOM3': '',
                      'CUSTOM4': '',
                      'CUSTOM5': '',
                      'CUSTOM6': '',
                      'CUSTOM7': '',
                      'CUSTOM8': '',
                      'ITEM': ''}

        if type == 'IEC61850':
            attribs = dev['attribs'].split('/')
            name_tag_attribs = '\\'.join(attribs)
            values = {'NAME': f"{dev['LD']}\\{dev['node']}\\{name_tag_attribs}",
                      'TYPE': dev['type'],
                      'UNIT': dev['io'],
                      'ADDR': f"{dev['LD']}/{dev['node']}${dev['fc']}${'$'.join(attribs)}",
                      'RAW_ZERO': '',
                      'RAW_FULL': '',
                      'ENG_ZERO': '',
                      'ENG_FULL': '',
                      'ENG_UNITS': '',
                      'FORMAT': '',
                      'COMMENT': dev['comment'],
                      'EDITCODE': '',
                      'LINKED': '',
                      'OID': '',
                      'REF1': '',
                      'REF2': '',
                      'DEADBAND': '',
                      'CUSTOM': '',
                      'TAGGENLINK': '',
                      'CLUSTER': self.cluster,
                      'HISTORIAN': 'TRUE',
                      'EQUIP': dev['equip'],
                      'CUSTOM1': '',
                      'CUSTOM2': '',
                      'CUSTOM3': '',
                      'CUSTOM4': '',
                      'CUSTOM5': '',
                      'CUSTOM6': '',
                      'CUSTOM7': '',
                      'CUSTOM8': '',
                      'ITEM': f"{dev['node']}\\{name_tag_attribs}"}

        return values

    def create_config61850(self, name_file):
        xml_doc = f"""
            <ScadaDevice xmlns="http://www.schneider-electric.com/SCADA/Drivers/IEC61850/DeviceConfig/v1/">
               <IPConnection>
                  <IP>127.0.0.1</IP>
                  <Port>102</Port>
               </IPConnection>
               <IED>TEMPLATE</IED>
               <LogicalDevice Name="Relay">
                  <BRCB>brcbEV1</BRCB>
                  <BRCB>brcbMX01</BRCB>
                  <URCB>urcbMX01</URCB>
               </LogicalDevice>
            </ScadaDevice>
            """

        soup = BeautifulSoup(xml_doc, 'lxml-xml')
        xml = soup.prettify()
        with open(self.get_path_file(name_file), "w") as file:
            file.write(xml)

    def get_path_file(self, name_file):
        return os.path.join(self.path_project, name_file)



project = Project('test61850_2')
project.copy_libfile(['libDevice.xlsx', 'setProject.xlsx'])
project.create_dbf_from_xls([('boards', 'NAME'), ('ports', 'NAME')])

project.create_eqtype()
project.create_io()
project.create_equip(isCreateTag=True)