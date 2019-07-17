import io
import json
import os
from collections import OrderedDict

from archetypal import load_idf, BuildingTemplate, GasMaterial, GlazingMaterial, \
    OpaqueMaterial, parallel_process, run_eplus, OpaqueConstruction, \
    WindowConstruction, StructureDefinition, DaySchedule, WeekSchedule, \
    YearSchedule, DomesticHotWaterSetting, VentilationSetting, ZoneConditioning, \
    ZoneConstructionSet, ZoneLoad, Zone, settings


class UmiTemplate:
    """

    """

    def __init__(self, name='unnamed', BuildingTemplates=None,
                 GasMaterials=None, GlazingMaterials=None,
                 OpaqueConstructions=None, OpaqueMaterials=None,
                 WindowConstructions=None, StructureDefinitions=None,
                 DaySchedules=None, WeekSchedules=None, YearSchedules=None,
                 DomesticHotWaterSettings=None, VentilationSettings=None,
                 WindowSettings=None, ZoneConditionings=None,
                 ZoneConstructionSets=None, ZoneLoads=None, Zones=None):
        """

        Args:
            name (str): The name of the template
            Zones (list of Zone):
            ZoneLoads (list of ZoneLoad):
            ZoneConstructionSets (list of ZoneConstructionSet):
            ZoneConditionings (list of ZoneConditioning):
            WindowSettings (list of WindowSetting):
            VentilationSettings (list of VentilationSetting):
            DomesticHotWaterSettings (list of DomesticHotWaterSetting):
            YearSchedules (list of YearSchedule):
            WeekSchedules (list of WeekSchedule):
            DaySchedules (list of DaySchedule):
            StructureDefinitions (list of StructureDefinition):
            WindowConstructions (list of WindowConstruction):
            OpaqueMaterials (list of OpaqueMaterial):
            OpaqueConstructions (list of OpaqueConstruction):
            GlazingMaterials (list of GlazingMaterial):
            GasMaterials (list of GasMaterial):
            BuildingTemplates (list of BuildingTemplate):
        """
        if Zones is None:
            Zones = []
        if ZoneLoads is None:
            ZoneLoads = []
        if ZoneConstructionSets is None:
            ZoneConstructionSets = []
        if ZoneConditionings is None:
            ZoneConditionings = []
        if WindowSettings is None:
            WindowSettings = []
        if VentilationSettings is None:
            VentilationSettings = []
        if DomesticHotWaterSettings is None:
            DomesticHotWaterSettings = []
        if YearSchedules is None:
            YearSchedules = []
        if WeekSchedules is None:
            WeekSchedules = []
        if DaySchedules is None:
            DaySchedules = []
        if StructureDefinitions is None:
            StructureDefinitions = []
        if WindowConstructions is None:
            WindowConstructions = []
        if OpaqueMaterials is None:
            OpaqueMaterials = []
        if OpaqueConstructions is None:
            OpaqueConstructions = []
        if GlazingMaterials is None:
            GlazingMaterials = []
        if GasMaterials is None:
            GasMaterials = []
        if BuildingTemplates is None:
            BuildingTemplates = []

        self.idfs = None
        self.idf_files = None
        self.name = name
        self.Zones = Zones
        self.ZoneLoads = ZoneLoads
        self.ZoneConstructionSets = ZoneConstructionSets
        self.ZoneConditionings = ZoneConditionings
        self.WindowSettings = WindowSettings
        self.VentilationSettings = VentilationSettings
        self.DomesticHotWaterSettings = DomesticHotWaterSettings
        self.YearSchedules = YearSchedules
        self.WeekSchedules = WeekSchedules
        self.DaySchedules = DaySchedules
        self.StructureDefinitions = StructureDefinitions
        self.WindowConstructions = WindowConstructions
        self.OpaqueMaterials = OpaqueMaterials
        self.OpaqueConstructions = OpaqueConstructions
        self.BuildingTemplates = BuildingTemplates
        self.GasMaterials = GasMaterials
        self.GlazingMaterials = GlazingMaterials

    @classmethod
    def from_idf(self, idf_files, weather, sql=None, load=False, name='unnamed',
                 load_idf_kwargs=None, run_eplus_kwargs=None):
        """Initializes a UmiTemplate class from one or more idf_files.

        Iterates over each building zones and creates corresponding objects
        from the building object to material objects.

        Args:
            idf_files (str or list):
            weather (str):
            load (bool):
            run_eplus_kwargs (dict):
            load_idf_kwargs (dict):
        """
        # instanciate class
        if run_eplus_kwargs is None:
            run_eplus_kwargs = {}
        if load_idf_kwargs is None:
            load_idf_kwargs = {}
        t = UmiTemplate(name)

        # fill in arguments
        t.idf_files = idf_files
        t.weather = weather
        t.sql = sql

        t.idfs = [load_idf(idf_file) for idf_file
                  in idf_files]

        # For each idf load
        gms, glazms, oms = [], [], []
        for idf in t.idfs:
            b = BuildingTemplate.from_idf(idf)
            # with each idf, append each objects
            gms.extend(GasMaterial.from_idf(idf))
            glazms.extend(GlazingMaterial.from_idf(idf))
            oms.extend(OpaqueMaterial.from_idf(idf))
        # use set() to remove duplicates
        t.GasMaterials.extend(set(gms))
        t.GlazingMaterials.extend(set(glazms))
        t.OpaqueMaterials.extend(set(oms))

        if load:
            rundict = {idf_file: dict(eplus_file=idf_file,
                                      weather_file=weather,
                                      output_report='sql',
                                      **run_eplus_kwargs) for idf_file in
                       idf_files}
            t.sql = parallel_process(rundict, run_eplus, use_kwargs=True)
            t.read()
            t.fill()

        return t

    def fill(self):
        # Todo: Finish enumerating all UmiTempalate objects

        if self.BuildingTemplates:
            for bt in self.BuildingTemplates:
                day_schedules = [bt.all_objects[obj]
                                 for obj in bt.all_objects
                                 if 'UmiSchedule' in obj]
                self.DaySchedules.extend(day_schedules)

                dhws = [bt.all_objects[obj]
                        for obj in bt.all_objects
                        if 'DomesticHotWaterSetting' in obj]
                self.DomesticHotWaterSettings.extend(dhws)

    def read(self):
        """Initialize UMI objects"""
        # Umi stuff
        in_dict = {idf.name: {'Name': idf.name,
                              'idf': idf,
                              'sql': idf.sql}
                   for idf in self.idfs
                   }
        for idf in in_dict:
            building_template = BuildingTemplate.from_idf(**in_dict[idf])
            self.BuildingTemplates.append(building_template)

    def run_eplus(self, idf_files, weather, **kwargs):
        """wrapper for :func:`run_eplus` function

        """
        sql_report = run_eplus(idf_files, weather, output_report='sql',
                               **kwargs)
        self.sql = sql_report

        return sql_report

    @classmethod
    def from_json(cls, filename):
        """Initializes a UmiTemplate class from a json file

        Args:
            filename (str):

        Returns:
            UmiTemplate: The template object
        """
        name = os.path.basename(filename)
        t = UmiTemplate(name)

        import json

        with open(filename, 'r') as f:
            datastore = json.load(f)

            # with datastore, create each objects
            t.GasMaterials = [GasMaterial.from_json(**store) for
                              store in datastore['GasMaterials']]
            t.GlazingMaterials = [GlazingMaterial(**store) for
                                  store in datastore["GlazingMaterials"]]
            t.OpaqueMaterials = [OpaqueMaterial(**store) for
                                 store in datastore["OpaqueMaterials"]]
            t.OpaqueConstructions = [
                OpaqueConstruction.from_json(
                    **store) for store in datastore["OpaqueConstructions"]]
            t.WindowConstructions = [
                WindowConstruction.from_json(
                    **store) for store in datastore["WindowConstructions"]]
            t.StructureDefinitions = [
                StructureDefinition.from_json(
                    **store) for store in datastore["StructureDefinitions"]]
            t.DaySchedules = [DaySchedule(**store)
                              for store in datastore["DaySchedules"]]
            t.WeekSchedules = [WeekSchedule.from_json(**store)
                               for store in datastore["WeekSchedules"]]
            t.YearSchedules = [YearSchedule.from_json(**store)
                               for store in datastore["YearSchedules"]]
            t.DomesticHotWaterSettings = [
                DomesticHotWaterSetting.from_json(**store)
                for store in datastore["DomesticHotWaterSettings"]]
            t.VentilationSettings = [
                VentilationSetting.from_json(**store)
                for store in datastore["VentilationSettings"]]
            t.ZoneConditionings = [
                ZoneConditioning.from_json(**store)
                for store in datastore["ZoneConditionings"]]
            t.ZoneConstructionSets = [
                ZoneConstructionSet.from_json(
                    **store) for store in datastore["ZoneConstructionSets"]]
            t.ZoneLoads = [ZoneLoad.from_json(**store)
                           for store in datastore["ZoneLoads"]]
            t.Zones = [Zone.from_json(**store)
                       for store in datastore["Zones"]]
            t.BuildingTemplates = [
                BuildingTemplate.from_json(**store)
                for store in datastore["BuildingTemplates"]]

            return t

    def to_json(self, path_or_buf=None, indent=2):
        """Writes the umi template to json format"""
        # todo: check is bools are created as lowercase 'false' pr 'true'

        if not path_or_buf:
            json_name = '%s.json' % self.name
            path_or_buf = os.path.join(settings.data_folder, json_name)
            # create the folder on the disk if it doesn't already exist
            if not os.path.exists(settings.data_folder):
                os.makedirs(settings.data_folder)
        with io.open(path_or_buf, 'w+', encoding='utf-8') as path_or_buf:
            data_dict = OrderedDict({'GasMaterials': [],
                                     'GlazingMaterials': [],
                                     'OpaqueMaterials': [],
                                     'OpaqueConstructions': [],
                                     'WindowConstructions': [],
                                     'StructureDefinitions': [],
                                     'DaySchedules': [],
                                     'WeekSchedules': [],
                                     'YearSchedules': [],
                                     'DomesticHotWaterSettings': [],
                                     'VentilationSettings': [],
                                     'ZoneConditionings': [],
                                     'ZoneConstructionSets': [],
                                     'ZoneLoads': [],
                                     'Zones': [],
                                     'WindowSettings': [],
                                     'BuildingTemplates': []})
            jsonized = []
            for bld in self.BuildingTemplates:
                all_objs = bld.all_objects
                for obj in all_objs:
                    if obj not in jsonized:
                        jsonized.append(obj)
                        catname = all_objs[obj].__class__.__name__ + 's'
                        app_dict = all_objs[obj].to_json()
                        data_dict[catname].append(app_dict)

            # Write the dict to json using json.dumps
            response = json.dumps(data_dict, indent=indent)
            path_or_buf.write(response)

        return response