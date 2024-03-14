import os
import shutil
import re

import dbf
import pandas as pd
from bs4 import BeautifulSoup
from dbfread import DBF
import numpy as np

from pandas.io.excel import ExcelWriter


class ProjectBases:

    def __init__(self, path_project):
        self.path_project = path_project
        self.base_equip = BaseProject(os.path.join(self.path_project, 'equip.DBF'))
        self.base_eqtype = BaseProject(os.path.join(self.path_project, 'eqtype.DBF'))
        self.base_io = BaseProject(os.path.join(self.path_project, 'units.DBF'))
        self.base_tag = BaseProject(os.path.join(self.path_project, 'variable.DBF'))
        self.base_trend = BaseProject(os.path.join(self.path_project, 'trend.DBF'))
        self.base_alarmAnalog = BaseProject(os.path.join(self.path_project, 'anaalm.DBF'))
        self.base_alarmDig = BaseProject(os.path.join(self.path_project, 'digalm.DBF'))
        self.base_pgdynobj = BaseProject(os.path.join(self.path_project, 'pgdynobj.DBF'))

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

    def to_dataframe_dbf(self, df):
        params_list = df.to_dict('records')
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
        self.path_projects = r"c:\ProgramData\AVEVA Plant SCADA 2020 R2\User"
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
        self.set_df_xls('df_tags', self.config_setProject_xls, 'Tag')

    def set_df_xls(self, name_df, config_xls, sheet_name):
        self.__dict__[name_df] = None
        try:
            df = pd.read_excel(config_xls, sheet_name=sheet_name)
            df = df.fillna('')
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
                    self.create_config61850(name_file_iec61850, isLDs=True)

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

    def create_equip(self, isCreateTag=False, typeCreateTag='simple', isCreateEquip=True, isCreateTags=True, isCreateTrendsAnalog=True, isCreateAlarmAnalog=True, isCreateAlarmDig=True):
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
                name_LD1 = name_LD;
                if equip['spec'].strip() != '': name_LD += f"_{equip['spec']}"

                name_equip = name_LD
                if equip['device'].strip() != '': name_equip += f"_{equip['device']}"

                values = {'NAME': name_equip,
                          'CLUSTER': self.cluster,
                          'TYPE': equip['device'],
                          'AREA': '',
                          'LOCATION': '',
                          'COMMENT': equip['comment'],
                          'CUSTOM1': name_LD,
                          # 'CUSTOM1': f"{equip['io']}\\",
                          'CUSTOM2': equip['CUSTOM2'],
                          'CUSTOM3': equip['CUSTOM3'],
                          'CUSTOM4': equip['CUSTOM4'],
                          'CUSTOM5': equip['CUSTOM5'],
                          'CUSTOM6': equip['CUSTOM6'],
                          'CUSTOM7': equip['CUSTOM7'],
                          'CUSTOM8': equip['CUSTOM8'],
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
                    df_dev['io'] = equip['io']
                    df_dev['LD'] = name_LD
                    df_dev['LD1'] = name_LD1
                    df_dev['equip'] = values['NAME']
                    self.create_tag(df_dev, type=typeCreateTag, isCreateTags=isCreateTags, isCreateTrendsAnalog=isCreateTrendsAnalog, isCreateAlarmAnalog=isCreateAlarmAnalog, isCreateAlarmDig=isCreateAlarmDig)
                    # self.create_tag(df_dev, type='IEC61850')

            if isCreateEquip: self.base.base_equip.to_dbf(params_list)

    def create_tag(self, df, type='simple', replace=None, isCreateTags=True, isCreateTrendsAnalog=True, isCreateAlarmAnalog=True, isCreateAlarmDig=True):
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
        df_trends = pd.DataFrame()
        df_alarmsAnalog = pd.DataFrame()
        df_alarmsDig = pd.DataFrame()

        if replace and len(df_tags_exist) != 0:
            df_tags = df_tags_exist

        if replace:
            self.base.base_tag.clear_dbf()
            self.base.base_trend.clear_dbf()
            self.base.base_trend.clear_dbf()

        for i in range(len(df)):
            dev = df.iloc[i]
            values = self.create_tag_values(dev, type=type)

            if values['NAME'] not in names:
                df_tags = pd.concat([df_tags, pd.DataFrame([values])], ignore_index=True)
                names.append(values['NAME'])
            else:
                if replace:
                    df_tags.loc[df_tags['NAME'] == values['NAME'], :] = list(values.values())

            if dev['type'] == 'REAL':
                if isCreateTrendsAnalog:
                    values = self.create_trend_values(dev, type)
                    df_trends = pd.concat([df_trends, pd.DataFrame([values])], ignore_index=True)

                if isCreateAlarmAnalog:
                    if dev['ENG_UNITS'] == 'V':
                        values = self.create_alarmAnalog_values(dev, type)
                        df_alarmsAnalog = pd.concat([df_alarmsAnalog, pd.DataFrame([values])], ignore_index=True)
            else:
                if isCreateAlarmDig:
                    values = self.create_alarmDig_values(dev, type)
                    df_alarmsDig = pd.concat([df_alarmsDig, pd.DataFrame([values])], ignore_index=True)

        if isCreateTags: self.base.base_tag.to_dataframe_dbf(df_tags)
        if isCreateTrendsAnalog: self.base.base_trend.to_dataframe_dbf(df_trends)
        if isCreateAlarmAnalog: self.base.base_alarmAnalog.to_dataframe_dbf(df_alarmsAnalog)
        if isCreateAlarmDig: self.base.base_alarmDig.to_dataframe_dbf(df_alarmsDig)

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
                      'CUSTOM1': dev['CUSTOM1'],
                      'CUSTOM2': dev['CUSTOM2'],
                      'CUSTOM3': dev['CUSTOM3'],
                      'CUSTOM4': dev['CUSTOM4'],
                      'CUSTOM5': dev['CUSTOM5'],
                      'CUSTOM6': dev['CUSTOM6'],
                      'CUSTOM7': dev['CUSTOM7'],
                      'CUSTOM8': dev['CUSTOM8'],
                      'ITEM': ''}

        if type == 'IEC61850_104':
            attribs = dev['attribs'].split('/')
            name_tag_attribs = '\\'.join(attribs)
            addr = f"{dev['LD']}/{dev['node']}${dev['fc']}${'$'.join(attribs)}"

            ls = self._getTagCommSw35(dev)
            nameTag = ls[0]
            comment = ls[1]

            if 'RZA' in dev['LD1']:
                numberRza = dev['LD1'].split('_')[1]
                nameTag = self._getnumsw35(nameTag, numberRza)
                comment = self._getnumsw35(comment, numberRza)

            unit = dev['io']
            if dev['attribs'] == '':
                addr = ''
                unit = 'Internal'
            values = {'NAME': nameTag,
                      'TYPE': dev['type'],
                      'UNIT': unit,
                      'ADDR': '',
                      'RAW_ZERO': '',
                      'RAW_FULL': '',
                      'ENG_ZERO': '',
                      'ENG_FULL': '',
                      'ENG_UNITS': f"{dev['ENG_UNITS']}",
                      'FORMAT': rf"{dev['FORMAT']}",
                      # 'FORMAT': "###.##",
                      'COMMENT': comment,
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
                      'CUSTOM1': dev['CUSTOM1'],
                      'CUSTOM2': dev['CUSTOM2'],
                      'CUSTOM3': dev['CUSTOM3'],
                      'CUSTOM4': dev['CUSTOM4'],
                      'CUSTOM5': dev['CUSTOM5'],
                      'CUSTOM6': dev['CUSTOM6'],
                      'CUSTOM7': dev['CUSTOM7'],
                      'CUSTOM8': dev['CUSTOM8'],
                      'ITEM': f"{dev['node']}\\{name_tag_attribs}"}

        if type == 'IEC61850':
            attribs = dev['attribs'].split('/')
            name_tag_attribs = '\\'.join(attribs)
            addr = f"{dev['LD']}/{dev['node']}${dev['fc']}${'$'.join(attribs)}"
            unit = dev['io']
            if dev['attribs'] == '':
                addr = ''
                unit = 'Internal'
            values = {'NAME': f"{dev['LD']}\\{dev['node']}\\{name_tag_attribs}",
                      'TYPE': dev['type'],
                      'UNIT': unit,
                      'ADDR': addr,
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
                      'CUSTOM1': dev['CUSTOM1'],
                      'CUSTOM2': dev['CUSTOM2'],
                      'CUSTOM3': dev['CUSTOM3'],
                      'CUSTOM4': dev['CUSTOM4'],
                      'CUSTOM5': dev['CUSTOM5'],
                      'CUSTOM6': dev['CUSTOM6'],
                      'CUSTOM7': dev['CUSTOM7'],
                      'CUSTOM8': dev['CUSTOM8'],
                      'ITEM': f"{dev['node']}\\{name_tag_attribs}"}

        return values

    def create_trend_values(self, df, type='simple'):
        '''

        :param df:
        :param type: 'simple', 'IEC61850'
        :return:
        '''
        dev = df.fillna('')

        values = {}

        attribs = dev['attribs'].split('/')
        name_tag_attribs = '\\'.join(attribs)

        values = {'NAME': f"{dev['LD1']}_{dev['name104']}",
                  'EXPR': f"{dev['LD1']}_{dev['name104']}",
                  'TRIG': '',
                  'SAMPLEPER': '00:00:05',
                  'PRIV': '',
                  'AREA': '',
                  'ENG_UNITS': dev['ENG_UNITS'],
                  'FORMAT': rf"{dev['FORMAT']}",
                  'FILENAME': '',
                  'FILES': '',
                  'TIME': '',
                  'PERIOD': '',
                  'COMMENT': dev['comment'],
                  'TYPE': 'TRN_PERIODIC',
                  'SPCFLAG': '',
                  'LSL': '',
                  'USL': '',
                  'SUBGRPSIZE': '',
                  'XDOUBLEBAR': '',
                  'RANGE': '',
                  'SDEVIATION': '',
                  'STORMETHOD': 'Floating Point (8-byte samples)',
                  'CLUSTER': self.cluster,
                  'TAGGENLINK': '',
                  'EQUIP': dev['equip'],
                  'EDITCODE': '',
                  'LINKED': '',
                  'DEADBAND': '',
                  'HISTORIAN': '',
                  'ITEM': f"{dev['node']}\\{name_tag_attribs}",
                  'ENG_ZERO': '',
                  'ENG_FULL': ''
                  }

        return values

    def create_alarmAnalog_values(self, df, type='simple'):
        '''

        :param df:
        :param type: 'simple', 'IEC61850'
        :return:
        '''
        dev = df.fillna('')

        values = {}

        attribs = dev['attribs'].split('/')
        name_tag_attribs = '\\'.join(attribs)

        ls = self._getTagCommSw35(dev)
        nameTag = ls[0]
        comment = ls[1]

        values = {
            'TAG': nameTag,
            'NAME': '',
            'VAR': nameTag,
            'SETPOINT': '',
            'HIGHHIGH': '6600',
            'HIGH': '',
            'LOW': '',
            'LOWLOW': '',
            'DEVIATION': '',
            'RATE': '',
            'DEADBAND': '',
            'FORMAT': rf"{dev['FORMAT']}",
            'CATEGORY': '_PLSALM_LOW',
            'HELP': '',
            'PRIV': '',
            'AREA': '',
            'COMMENT': comment,
            'SEQUENCE': '',
            'HHDELAY': '',
            'HDELAY': '',
            'LDELAY': '',
            'LLDELAY': '',
            'DEVDELAY': '',
            'CUSTOM1': '',
            'CUSTOM2': '',
            'CUSTOM3': '',
            'CUSTOM4': '',
            'CUSTOM5': '',
            'CUSTOM6': '',
            'CUSTOM7': '',
            'CUSTOM8': '',
            'CLUSTER': self.cluster,
            'TAGGENLINK': '',
            'PAGING': '',
            'PAGINGGRP': '',
            'EDITCODE': '',
            'LINKED': '',
            'HISTORIAN': '',
            'EQUIP': dev['equip'],
            'ITEM': f"{dev['node']}\\{name_tag_attribs}"
                  }

        return values

    def create_alarmDig_values(self, df, type='simple'):
        '''

        :param df:
        :param type: 'simple', 'IEC61850'
        :return:
        '''
        dev = df.fillna('')

        values = {}

        attribs = dev['attribs'].split('/')
        name_tag_attribs = '\\'.join(attribs)

        desc = 'Да,Нет'
        if dev['CUSTOM6'] in ['увімкнено', 'в робочому']:
            desc = 'Вкл,Выкл'

        cat = '_PLSALM_EVENT'
        if dev['CUSTOM5'] == 'PR':
            cat = '_PLSALM_HIGH'
        if dev['CUSTOM5'] == 'FL':
            cat = '_PLSALM_MEDIUM'
        if dev['fc'] == 'MX':
            cat = '_PLSALM_EVENT'

        comment = dev['comment']

        ls = self._getTagCommSw35(dev)
        nameTag = ls[0]
        comment = ls[1]

        values = {
            'TAG': nameTag,
            'NAME': comment,
            'DESC': desc,
            'VAR_A': nameTag,
            'VAR_B': "",
            'CATEGORY': cat,
            'HELP': '',
            'PRIV': '',
            'AREA': '',
            'COMMENT': comment,
            'SEQUENCE': '',
            'DELAY': '',
            'CUSTOM1': '',
            'CUSTOM2': '',
            'CUSTOM3': '',
            'CUSTOM4': '',
            'CUSTOM5': '',
            'CUSTOM6': '',
            'CUSTOM7': '',
            'CUSTOM8': '',
            'CLUSTER': self.cluster,
            'TAGGENLINK': '',
            'PAGING': '',
            'PAGINGGRP': '',
            'EDITCODE': '',
            'LINKED': '',
            'HISTORIAN': '',
            'EQUIP': dev['equip'],
            'ITEM': f"{dev['node']}\\{name_tag_attribs}"
                  }

        return values

    def create_config61850(self, name_file, isLDs=False):

        s1 = ""

        if isLDs:
            lds = []
            if self.df_equips is not None:
                for i in range(len(self.df_equips)):
                    equip = self.df_equips.iloc[i]

                    name_LD = f"{equip['name']}"
                    if equip['number'].strip() != '': name_LD += f"_{equip['number']}"
                    if equip['spec'].strip() != '': name_LD += f"_{equip['spec']}"
                    lds.append(name_LD)
                    s1 += f"""
                            <LogicalDevice Name="{name_LD}">
                                  <BRCB>brcbEV1</BRCB>
                                  <BRCB>brcbEV2</BRCB>
                                  <URCB>urcbEV1</URCB>
                               </LogicalDevice>

                        """
            else:
                f"""
                    <LogicalDevice Name="Relay">
                          <BRCB>brcbEV1</BRCB>
                          <BRCB>brcbEV2</BRCB>
                          <URCB>urcbEV1</URCB>
                       </LogicalDevice>
                """

        xml_doc = f"""
            <ScadaDevice xmlns="http://www.schneider-electric.com/SCADA/Drivers/IEC61850/DeviceConfig/v1/">
               <IPConnection>
                  <IP>127.0.0.1</IP>
                  <Port>102</Port>
               </IPConnection>
               <IED>TEMPLATE</IED>
               {s1}
            </ScadaDevice>
            """

        soup = BeautifulSoup(xml_doc, 'lxml-xml')
        xml = soup.prettify()
        with open(self.get_path_file(name_file), "w", encoding='utf-8') as file:
            file.write(xml)

    def get_path_file(self, name_file):
        return os.path.join(self.path_project, name_file)

    def create_ci_file_sql(self):

        df1 = self.base.base_tag.dataframe()
        sr = df1[df1['TYPE'] == 'REAL']
        last_index = sr.tail(1).index.item()

        ls_sql_insert_col = []
        ls_sql_insert_val = []
        ls_sql_create = []
        ls_map = []
        cols = []
        for i, tag in sr.iterrows():
            # match = re.search(r'(\S+)_(\S+)_(\S+?)\\', tag)
            match = re.search(r'(\S+)_(\S+)_(\S+)_(\S+)_(\S+)', tag['EQUIP'])
            x1 = match.group(1)
            x2 = match.group(2)
            x4 = '_'.join(tag['NAME'].split('_')[2:])


            shkaf_name = 's'
            if x1 == 'RZA': shkaf_name = 'r'
            if x1 == 'Cell': shkaf_name = 'c'

            col = f'{shkaf_name}{x2}_{x4}'
            cols.append(col)

            # Map------------------------------------------------------------------
            ls_map.append(rf'MapValueSet(sm1, "{col}",  RealToStr({tag.NAME}, 5, 2, "."));')
            ls_map.append(rf'MapValueSet(sm1, "{col}_t", getTimeTag("{tag.NAME}"));')
            ls_map.append(rf'MapValueSet(sm1, "{col}_q", getQualityTag("{tag.NAME}"));')

            # sql insert---------------------------------------------------------------
            ls_sql_insert_val.append(f'SQLAppend(hSQL, MapValueGet(smap1 , "{col}") + ",");')
            ls_sql_insert_val.append(f'''SQLAppend(hSQL, "'" + MapValueGet(smap1 , "{col}_t") + "',");''')
            # ls_sql_insert_val.append(f'''SQLAppend(hSQL, MapValueGet(smap1 , "{col_base}t") + ",");''')

            ls_sql_insert_col.append(f'SQLAppend(hSQL, "{col},");')
            ls_sql_insert_col.append(f'SQLAppend(hSQL, "{col}_t,");')

            if i == last_index:
                ls_sql_insert_val.append(f'''SQLAppend(hSQL, "'" + MapValueGet(smap1 , "{col}_q") + "'");''')
                # ls_sql_insert_val.append(f'''SQLAppend(hSQL, MapValueGet(smap1 , "{col_base}q"));''')
                ls_sql_insert_col.append(f'SQLAppend(hSQL, "{col}_q");')
            else:
                ls_sql_insert_val.append(f'''SQLAppend(hSQL, "'" + MapValueGet(smap1 , "{col}_q") + "',");''')
                # ls_sql_insert_val.append(f'''SQLAppend(hSQL, MapValueGet(smap1 , "{col_base}q") + ",");''')
                ls_sql_insert_col.append(f'SQLAppend(hSQL, "{col}_q,");')

            # sql create----------------------------------------------------------------
            ls_sql_create.append(f'{col} real,')
            ls_sql_create.append(f'{col}_t datetime,')
            ls_sql_create.append(f'{col}_q NVARCHAR(20),')

        with open(os.path.join(self.path_project, 'AnalgSql_Map.ci'), 'w') as f:
            f.write('STRING FUNCTION AnalgSql_Map()\n')
            f.write('   STRING sm1 = MapOpen();\n')
            f.write('   MapValueSet(sm1, "date", getTimeCurrent());\n\n')
            for item in ls_map:
                f.write(f'  {item}\n')
            f.write('\n   RETURN sm1;\n')
            f.write('END')

        with open(os.path.join(self.path_project, 'AnalgSql_Insert.ci'), 'w') as f:
            f.write('FUNCTION AnalgSql_AppendCol(INT hSQL)\n')
            for item in ls_sql_insert_col:
                f.write(f'  {item}\n')
            f.write('END')
            f.write('\n\n')

            f.write('FUNCTION AnalgSql_AppendVal(INT hSQL, STRING smap1)\n')
            for item in ls_sql_insert_val:
                f.write(f'  {item}\n')
            f.write('END')

        with open(os.path.join(self.path_project, 'AnalgSql_Insert.sql'), 'w') as f:
            f.write('DROP TABLE mmxu_s;\n')
            f.write('DROP TABLE mmxu_m;\n')
            f.write('DROP TABLE mmxu_h;\n')

            f.write('CREATE TABLE mmxu_s\n(')
            f.write('dt datetime PRIMARY KEY,\n')
            for item in ls_sql_create:
                f.write(f'  {item}\n')
            f.write(');\n')

            f.write('CREATE TABLE mmxu_m\n(')
            f.write('dt datetime PRIMARY KEY,\n')
            for item in ls_sql_create:
                f.write(f'  {item}\n')
            f.write(');\n')

            f.write('CREATE TABLE mmxu_h\n(')
            f.write('dt datetime PRIMARY KEY,\n')
            for item in ls_sql_create:
                f.write(f'  {item}\n')
            f.write(');\n')

    def create_ci_file_simul(self):

        df1 = self.base.base_tag.dataframe()
        sr = df1[df1['TYPE'] == 'REAL']
        ls = []
        for i, tag in sr.iterrows():
            if '_u' in tag['NAME'] or '_U' in tag['NAME']:
                ls.append(f'Rand_analg_int("{tag.NAME}", 1000, 5500);')
            if '_i' in tag['NAME']:
                ls.append(f'Rand_analg("{tag.NAME}", 10, 9);')
            if '_F' in tag['NAME']:
                ls.append(f'Rand_analg("{tag.NAME}", 20, 40);')
            if '_T' in tag['NAME']:
                ls.append(f'Rand_analg_int("{tag.NAME}", 40, 50);')
        s5 = '\n'.join(ls)

        with open(os.path.join(self.path_project, 'VS_Simul.ci'), 'w') as f:
            f.write('FUNCTION SimulAnalog()\n')
            for item in ls:
                f.write(f'  {item}\n')
            f.write('END')

            # ----------------------------------------------------------------
            f.write('\n\n')

            f.write('FUNCTION sim_createMapI()\n')
            f.write(f'  STRING smp;\n\n')

            for item in list(sr['NAME'].values):
                tt = item.split('_')
                section = 1
                if tt[0] == 'Cell' and int(tt[1]) > 11:
                    section = 2;
                if tt[0] == 'RZA' and int(tt[1]) < 3:
                    section = 2;
                f.write(f'  smp = MapOpen();\n')
                f.write(f'  MapValueSet(smp, "SW", 1);\n')
                f.write(f'  MapValueSet(smp, "section", {section});\n')
                f.write(f'  MapValueSet(mapSimTagAnalToZero, "{item}", smp);\n')
                f.write(f'\n')
            f.write('END')

            # ----------------------------------------------------------------
            f.write('\n\n')

            f.write('FUNCTION sim_initMapI_1()\n')

            for i in range(2,12):
                ls1 = sr[sr['NAME'].str.contains(f'Cell_{i}_i')]['NAME'].values.tolist()
                if len(ls1) > 0:
                    f.write(f'  IF NOT Cell_{i}_SW_pos THEN\n')
                    for tag in ls1:
                        f.write(f'      MapValueSet(MapValueGet(mapSimTagAnalToZero, "{tag}"), "SW", 0);\n')
                    f.write(f'  END\n\n')

            f.write(
            '''
    IF tireSection35kB_1 = 0 THEN
        MapValueSet(MapValueGet(mapSimTagAnalToZero, "RZA_4_iA"), "SW", 0);
        MapValueSet(MapValueGet(mapSimTagAnalToZero, "RZA_4_iB"), "SW", 0);
        MapValueSet(MapValueGet(mapSimTagAnalToZero, "RZA_4_iC"), "SW", 0);
    END
        
    IF tireSection35kB_1_SW2 = 0 THEN
        MapValueSet(MapValueGet(mapSimTagAnalToZero, "RZA_5_iA"), "SW", 0);
        MapValueSet(MapValueGet(mapSimTagAnalToZero, "RZA_5_iB"), "SW", 0);
        MapValueSet(MapValueGet(mapSimTagAnalToZero, "RZA_5_iC"), "SW", 0);
    END
    
    IF tireSection35kB_CB_1 = 0 THEN
        MapValueSet(MapValueGet(mapSimTagAnalToZero, "RZA_3_iA"), "SW", 0);
        MapValueSet(MapValueGet(mapSimTagAnalToZero, "RZA_3_iB"), "SW", 0);
        MapValueSet(MapValueGet(mapSimTagAnalToZero, "RZA_3_iC"), "SW", 0);
    END
            ''')

            f.write('\nEND')

            # ----------------------------------------------------------------
            f.write('\n\n')

            f.write('FUNCTION sim_initMapI_2()\n')

            for i in range(13, 22):
                ls1 = sr[sr['NAME'].str.contains(f'Cell_{i}_i')]['NAME'].values.tolist()
                if len(ls1) > 0:
                    f.write(f'  IF NOT Cell_{i}_SW_pos THEN\n')
                    for tag in ls1:
                        f.write(f'      MapValueSet(MapValueGet(mapSimTagAnalToZero, "{tag}"), "SW", 0);\n')
                    f.write(f'  END\n\n')

            f.write(
                '''
    IF tireSection35kB_2 = 0 THEN
        MapValueSet(MapValueGet(mapSimTagAnalToZero, "RZA_1_iA"), "SW", 0);
        MapValueSet(MapValueGet(mapSimTagAnalToZero, "RZA_1_iB"), "SW", 0);
        MapValueSet(MapValueGet(mapSimTagAnalToZero, "RZA_1_iC"), "SW", 0);
    END
        
    IF tireSection35kB_2_SW2 = 0 THEN
        MapValueSet(MapValueGet(mapSimTagAnalToZero, "RZA_2_iA"), "SW", 0);
        MapValueSet(MapValueGet(mapSimTagAnalToZero, "RZA_2_iB"), "SW", 0);
        MapValueSet(MapValueGet(mapSimTagAnalToZero, "RZA_2_iC"), "SW", 0);
    END
                ''')

            f.write('\nEND')


    def create_ci_file_sql_OLD(self):

        df1 = self.base.base_tag.dataframe()
        sr = df1[(df1['ITEM'].str.contains(r'MMXU')) | (df1['ITEM'].str.contains(r'CtlV\\'))]
        sr = sr[~((sr['ITEM'].str.contains(r'\\t')) | (sr['ITEM'].str.contains(r'\\q')) | (
            sr['ITEM'].str.contains(r'\\T')))]

        last_index = sr.tail(1).index.item()

        ds = {
            'TH6': 'tn',
            'LN6': 'ln',
            'IN6': 'in',
            'CB6': 'cb',
            'T1': 't1',
            'T2': 't2',
            'CB35': 'cb',
            'RPN1': 'rpn1',
            'RPN2': 'rpn2',
        }

        ls_sql_insert_col = []
        ls_sql_insert_val = []
        ls_sql_create = []
        ls_map = []
        cols = []
        for i, tag in sr.iterrows():
            # match = re.search(r'(\S+)_(\S+)_(\S+?)\\', tag)
            match = re.search(r'(\S+)_(\S+)_(\S+)_(\S+)_(\S+)', tag['EQUIP'])
            match1 = re.search(r'(\S+)\\(\S+$)', tag['ITEM'])
            x1 = match.group(1)
            x2 = match.group(2)
            x3 = match.group(3)
            x4 = match1.group(2)

            shkaf_name = 'c'
            if x1 == 'RZA': shkaf_name = 'r'

            val = ''
            if 'phsAB\\' in tag['ITEM']: val = 'uab'
            if 'phsBC\\' in tag['ITEM']: val = 'ubc'
            if 'phsCA\\' in tag['ITEM']: val = 'uca'
            if 'CtlV\\' in tag['ITEM']: val = 'u'
            if 'phsA\\' in tag['ITEM']: val = 'ia'
            if 'phsB\\' in tag['ITEM']: val = 'ib'
            if 'phsC\\' in tag['ITEM']: val = 'ic'
            if 'A\\neut' in tag['ITEM']: val = '3io'
            if 'PhV\\neut' in tag['ITEM']: val = '3uo'
            if 'Hz' in tag['ITEM']: val = 'hz'

            col_base = f'{shkaf_name}{x2}_{ds[x3]}_{val}_'
            col = f'{shkaf_name}{x2}_{ds[x3]}_{val}_{x4}'
            cols.append(col)

            # Map------------------------------------------------------------------
            ls_map.append(rf'MapValueSet(sm1, "{col}",  RealToStr({tag.NAME}, 5, 2, "."));')
            ls_map.append(rf'MapValueSet(sm1, "{col_base}t", getTimeTag("{tag.NAME}.Field"));')
            ls_map.append(rf'MapValueSet(sm1, "{col_base}q", getQualityTag("{tag.NAME}.Field"));')

            # sql insert---------------------------------------------------------------
            ls_sql_insert_val.append(f'SQLAppend(hSQL, MapValueGet(smap1 , "{col}") + ",");')
            ls_sql_insert_val.append(f'''SQLAppend(hSQL, "'" + MapValueGet(smap1 , "{col_base}t") + "',");''')
            # ls_sql_insert_val.append(f'''SQLAppend(hSQL, MapValueGet(smap1 , "{col_base}t") + ",");''')

            ls_sql_insert_col.append(f'SQLAppend(hSQL, "{col},");')
            ls_sql_insert_col.append(f'SQLAppend(hSQL, "{col_base}t,");')

            if i == last_index:
                ls_sql_insert_val.append(f'''SQLAppend(hSQL, "'" + MapValueGet(smap1 , "{col_base}q") + "'");''')
                # ls_sql_insert_val.append(f'''SQLAppend(hSQL, MapValueGet(smap1 , "{col_base}q"));''')
                ls_sql_insert_col.append(f'SQLAppend(hSQL, "{col_base}q");')
            else:
                ls_sql_insert_val.append(f'''SQLAppend(hSQL, "'" + MapValueGet(smap1 , "{col_base}q") + "',");''')
                # ls_sql_insert_val.append(f'''SQLAppend(hSQL, MapValueGet(smap1 , "{col_base}q") + ",");''')
                ls_sql_insert_col.append(f'SQLAppend(hSQL, "{col_base}q,");')

            # sql create----------------------------------------------------------------
            ls_sql_create.append(f'{col} real,')
            ls_sql_create.append(f'{col_base}t datetime,')
            ls_sql_create.append(f'{col_base}q NVARCHAR(20),')

        with open(os.path.join(self.path_project, 'AnalgSql_Map.ci'), 'w') as f:
            f.write('STRING FUNCTION AnalgSql_Map()\n')
            f.write('   STRING sm1 = MapOpen();\n')
            f.write('   MapValueSet(sm1, "date", getTimeCurrent());\n\n')
            for item in ls_map:
                f.write(f'  {item}\n')
            f.write('\n   RETURN sm1;\n')
            f.write('END')

        with open(os.path.join(self.path_project, 'AnalgSql_Insert.ci'), 'w') as f:
            f.write('FUNCTION AnalgSql_AppendCol(INT hSQL)\n')
            for item in ls_sql_insert_col:
                f.write(f'  {item}\n')
            f.write('END')
            f.write('\n\n')

            f.write('FUNCTION AnalgSql_AppendVal(INT hSQL, STRING smap1)\n')
            for item in ls_sql_insert_val:
                f.write(f'  {item}\n')
            f.write('END')

        with open(os.path.join(self.path_project, 'AnalgSql_Insert.sql'), 'w') as f:
            f.write('DROP TABLE mmxu_s;\n')
            f.write('DROP TABLE mmxu_m;\n')
            f.write('DROP TABLE mmxu_h;\n')

            f.write('CREATE TABLE mmxu_s\n(')
            f.write('dt datetime PRIMARY KEY,\n')
            for item in ls_sql_create:
                f.write(f'  {item}\n')
            f.write(');\n')

            f.write('CREATE TABLE mmxu_m\n(')
            f.write('dt datetime PRIMARY KEY,\n')
            for item in ls_sql_create:
                f.write(f'  {item}\n')
            f.write(');\n')

            f.write('CREATE TABLE mmxu_h\n(')
            f.write('dt datetime PRIMARY KEY,\n')
            for item in ls_sql_create:
                f.write(f'  {item}\n')
            f.write(');\n')

    def _getTagCommSw35(self, df):
        nameTag = f"{df['LD1']}_{df['name104']}"
        comment = df['comment']

        if 'RZA' in df['LD1']:
            numberRza = df['LD1'].split('_')[1]
            nameTag = self._getnumsw35(nameTag, numberRza)
            comment = self._getnumsw35(comment, numberRza)
        return [nameTag, comment]

    def _getnumsw35(self, name, numberRza):
        if '@' in name:
            ix = name.index('@')
            num = name[ix + 1:ix + 2]
            if numberRza in ['1', '2']:
                num = str(int(num) + 1)
            sub_old = name[ix:ix + 2]
            name = name.replace(sub_old, num)
        return name