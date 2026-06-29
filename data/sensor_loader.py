"""
Load and parse sensor data from CSV and Excel files.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np

class SensorDataLoader:
    """Load sensor observations from CSV files."""

    DATA_DIR = Path(__file__).parent.parent / 'datasets'

    SENSOR_SPECS = {
        'radar': {
            'file': 'mock_radar_observations_1hour.csv',
            'name': 'RADAR Sensor',
            'description': 'Motion detection and object tracking',
            'capabilities': [
                'Motion Detection (Velocity Analysis)',
                'Object Classification (Person, Vehicle, Drone)',
                'Speed Measurement',
                'Range Estimation',
                'Threat Assessment',
            ],
            'uses': ['Detect moving obstacles', 'Track trajectories', 'Measure velocity', 'Classify object types'],
        },
        'thermal': {
            'file': 'mock_thermal_observations_1hour.csv',
            'name': 'THERMAL Camera',
            'description': 'Infrared imaging and heat detection',
            'capabilities': [
                'Night Vision Navigation',
                'Heat Signature Detection',
                'Thermal Anomaly Detection',
                'Occlusion Detection',
                'Organism Identification',
            ],
            'uses': ['Navigate in darkness', 'Detect organisms', 'Find geothermal sources', 'Assess visibility'],
        },
        'lidar': {
            'file': 'mock_lidar_observations_1hour.csv',
            'name': 'LIDAR Scanner',
            'description': '3D point cloud and obstacle mapping',
            'capabilities': [
                '3D Terrain Mapping',
                'Obstacle Detection',
                'Precision Positioning',
                'Path Planning',
                'SLAM (Localization and Mapping)',
            ],
            'uses': ['Create 3D maps', 'Avoid obstacles', 'Plan routes', 'Build environment models'],
        },
        'env_probe': {
            'files': [
                'Mock_Lunar_Environment_Dataset_2026-06-29_1200.xlsx',
                'lunar_env_probe_1hour.csv',
                'mock_env_probe_1hour.csv',
            ],
            'sheet_name': 'Lunar_Environment',
            'name': 'Environmental Probe Pack',
            'description': 'Excel-backed lunar environment readings with temperature, pressure, radiation, and derived dust/EC signals',
            'capabilities': [
                'Atmospheric Profiling (Temp/Humidity/Pressure)',
                'Air Quality Analysis (Absorbance & Scattering)',
                'Cosmic Radiation Monitoring',
                'Electrical Conductivity Survey',
                'Dust & Particulate Monitoring (PM2.5)',
            ],
            'uses': ['Monitor atmospheric conditions', 'Detect dust storms', 'Track radiation exposure', 'Assess soil conductivity'],
        },
        'xrd': {
            'file': 'mock_xrd_observations_1hour.csv',
            'name': 'X-Ray Diffraction (XRD)',
            'description': 'Mineral phase identification via diffraction patterns',
            'capabilities': [
                'Mineral Phase Identification',
                'Crystallinity Index Measurement',
                'Amorphous Fraction Estimation',
                'Multi-mineral Composition',
                'Crystallographic Peak Analysis',
            ],
            'uses': ['Identify rock-forming minerals', 'Quantify mineral phases', 'Detect alteration products', 'Map regolith composition'],
        },
        'xrf': {
            'file': 'mock_xrf_observations_1hour.csv',
            'name': 'X-Ray Fluorescence (XRF)',
            'description': 'Elemental composition of rocks and regolith',
            'capabilities': [
                'Major Element Analysis (Si, Al, Fe, Ca, Mg)',
                'Trace Element Detection (Cr, Ni, Sr, Zr)',
                'Geochemical Classification',
                'Regolith Maturity Index',
                'Elemental Ratio Calculation',
            ],
            'uses': ['Determine rock type by chemistry', 'Find rare elements', 'Classify igneous vs sedimentary', 'Track weathering'],
        },
        'gpr': {
            'file': 'mock_gpr_observations_1hour.csv',
            'name': 'Ground Penetrating Radar (GPR)',
            'description': 'Sub-surface structure detection to ~12m depth',
            'capabilities': [
                'Lava Tube Detection (Void Mapping)',
                'Underground Ice Detection',
                'Stratigraphic Layer Mapping',
                'Fracture System Identification',
                'Regolith Depth Profiling',
            ],
            'uses': ['Find lava tubes for shelter', 'Locate subsurface ice', 'Map geological layers', 'Assess ground stability'],
        },
        'ph': {
            'file': 'mock_ph_observations_1hour.csv',
            'name': 'pH Probe',
            'description': 'Regolith and soil acidity/alkalinity measurement',
            'capabilities': [
                'pH Measurement (Acidity/Alkalinity)',
                'Oxidation-Reduction Potential (ORP)',
                'Ionic Strength Estimation',
                'Buffer Capacity Analysis',
                'Depth-Profile pH Mapping',
            ],
            'uses': ['Assess habitability', 'Detect chemical weathering', 'Evaluate biosignature potential', 'Map acidic zones'],
        },
        'soil_core': {
            'files': [
                'FINAL_mock_lunar_soil_core_sampler_0_15cm_observations_1hour.xlsx',
                'final_soil_core_1hour.csv',
            ],
            'name': 'Soil Core Sampler (0–15 cm)',
            'description': 'Final lunar soil-core dataset with drillability, density, moisture, and volatile indicators',
            'capabilities': [
                'Bulk Density Measurement',
                'Porosity & Moisture Content',
                'Volatile Detection',
                'Texture & Drillability Analysis',
                'Stratigraphic Layering (0–15 cm)',
            ],
            'uses': ['Characterize regolith structure', 'Assess trafficability & drillability', 'Detect trapped volatiles', 'Sample for lab analysis'],
        },
        'gas': {
            'file': 'mock_gas_syringe_1hour.csv',
            'name': 'Gas Syringe Sampler',
            'description': 'Atmospheric and soil gas composition analysis',
            'capabilities': [
                'Atmospheric Gas Composition (N2/O2/Ar/CO2)',
                'Trace Gas Detection (CH4, H2S, SO2, N2O)',
                'Soil Respiration Measurement',
                'Volatile Organic Compound (VOC) Profiling',
                'Gas Source Comparison (Atm vs Soil)',
            ],
            'uses': ['Detect outgassing features', 'Monitor CO2 flux', 'Find methane seeps', 'Characterise soil gas environment'],
        },
    }

    # Authoritative test list — maps each sensor to the EXACT analysis_type keys
    # that perform_analysis() dispatches on, with display names. This is what the
    # capabilities endpoint returns so the UI always sends a runnable type.
    SENSOR_TESTS = {
        'radar': [
            ('motion_detection',   'Motion Detection (Velocity Analysis)'),
            ('object_classification', 'Object Classification'),
            ('threat_assessment',  'Threat Assessment'),
            ('range_analysis',     'Range Estimation'),
        ],
        'thermal': [
            ('night_navigation',   'Night Vision Navigation'),
            ('heat_signature',     'Heat Signature Detection'),
            ('thermal_anomalies',  'Thermal Anomaly Detection'),
            ('occlusion_detection','Occlusion Detection'),
        ],
        'lidar': [
            ('3d_mapping',         '3D Terrain Mapping'),
            ('obstacle_detection', 'Obstacle Detection'),
            ('path_planning',      'Path Planning'),
            ('slam',               'SLAM (Localization & Mapping)'),
        ],
        'env_probe': [
            ('atmospheric_profiling',         'Atmospheric Profiling (Temp/Humidity/Pressure)'),
            ('air_quality_analysis',          'Air Quality Analysis (Absorbance & Scattering)'),
            ('cosmic_radiation_monitoring',   'Cosmic Radiation Monitoring'),
            ('electrical_conductivity_survey','Electrical Conductivity Survey'),
            ('dust_particulate_monitoring',   'Dust & Particulate Monitoring (PM2.5)'),
        ],
        'xrd': [
            ('mineral_phase_identification',  'Mineral Phase Identification'),
            ('crystallinity_index_measurement','Crystallinity Index Measurement'),
            ('amorphous_fraction_estimation', 'Amorphous Fraction Estimation'),
            ('multi_mineral_composition',     'Multi-mineral Composition'),
            ('crystallographic_peak_analysis','Crystallographic Peak Analysis'),
        ],
        'xrf': [
            ('major_element_analysis',  'Major Element Analysis (Si, Al, Fe, Ca, Mg)'),
            ('trace_element_detection', 'Trace Element Detection (Cr, Ni, Sr, Zr)'),
            ('geochemical_classification','Geochemical Classification'),
            ('regolith_maturity_index', 'Regolith Maturity Index'),
            ('elemental_ratio_calculation','Elemental Ratio Calculation'),
        ],
        'gpr': [
            ('lava_tube_detection',        'Lava Tube Detection (Void Mapping)'),
            ('underground_ice_detection',  'Underground Ice Detection'),
            ('stratigraphic_layer_mapping','Stratigraphic Layer Mapping'),
            ('fracture_system_identification','Fracture System Identification'),
            ('regolith_depth_profiling',   'Regolith Depth Profiling'),
        ],
        'ph': [
            ('ph_measurement',             'pH Measurement (Acidity/Alkalinity)'),
            ('oxidation_reduction_potential','Oxidation-Reduction Potential (ORP)'),
            ('ionic_strength_estimation',  'Ionic Strength Estimation'),
            ('buffer_capacity_analysis',   'Buffer Capacity Analysis'),
            ('depth_profile_ph_mapping',   'Depth-Profile pH Mapping'),
        ],
        'soil_core': [
            ('bulk_density_measurement',   'Bulk Density Measurement'),
            ('porosity_moisture_content',  'Porosity & Moisture Content'),
            ('volatile_detection',         'Volatile Detection'),
            ('texture_compaction_analysis','Texture & Drillability Analysis'),
            ('stratigraphic_layering',     'Stratigraphic Layering (0–15 cm)'),
        ],
        'gas': [
            ('atmospheric_gas_composition','Atmospheric Gas Composition (N2/O2/Ar/CO2)'),
            ('trace_gas_detection',        'Trace Gas Detection (CH4, H2S, SO2, N2O)'),
            ('soil_respiration_measurement','Soil Respiration Measurement'),
            ('voc_profiling',              'Volatile Organic Compound (VOC) Profiling'),
            ('gas_source_comparison',      'Gas Source Comparison (Atm vs Soil)'),
        ],
    }

    @staticmethod
    def _read_tabular_file(path: Path, sheet_name=0):
        """Read a CSV or Excel file based on the file suffix."""
        suffix = path.suffix.lower()
        if suffix in {'.xlsx', '.xls', '.xlsm'}:
            return pd.read_excel(path, sheet_name=sheet_name)
        return pd.read_csv(path)

    @staticmethod
    def _load_first_available(files, sheet_name=0):
        """Load the first readable file from a candidate list."""
        for name in files:
            path = SensorDataLoader.DATA_DIR / name
            if not path.exists():
                continue
            try:
                return SensorDataLoader._read_tabular_file(path, sheet_name=sheet_name)
            except (PermissionError, OSError, ValueError):
                continue
        return None

    @staticmethod
    def _normalize_env_probe(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize lunar environment columns to the dashboard schema."""
        if df is None or df.empty:
            return df

        def _series_or_default(column_name, default=0.0):
            if column_name in df.columns:
                return pd.to_numeric(df[column_name], errors='coerce')
            return pd.Series(default, index=df.index, dtype='float64')

        rename = {
            'Timestamp (UTC)': 'timestamp',
            'Lunar Time': 'lunar_time',
            'Ambient Temp (°C)': 'temp_c',
            'Regolith Temp 5cm (°C)': 'regolith_5cm_c',
            'Regolith Temp 50cm (°C)': 'regolith_50cm_c',
            'Rover Internal Temp (°C)': 'rover_internal_temp_c',
            'Solar Illumination (%)': 'solar_pct',
            'Humidity (%)': 'humidity_pct',
            'Pressure (Pa)': 'pressure_pa',
            'Radiation (µSv/h)': 'cosmic_rad_usv_h',
            'Location': 'location',
        }
        df = df.rename(columns=rename).copy()
        if 'temp_c' not in df.columns:
            fallback_rename = {}
            for column in df.columns:
                column_lower = str(column).strip().lower()
                if column_lower.startswith('timestamp'):
                    fallback_rename[column] = 'timestamp'
                elif column_lower.startswith('lunar time'):
                    fallback_rename[column] = 'lunar_time'
                elif 'ambient temp' in column_lower:
                    fallback_rename[column] = 'temp_c'
                elif 'regolith temp 5cm' in column_lower:
                    fallback_rename[column] = 'regolith_5cm_c'
                elif 'regolith temp 50cm' in column_lower:
                    fallback_rename[column] = 'regolith_50cm_c'
                elif 'rover internal temp' in column_lower:
                    fallback_rename[column] = 'rover_internal_temp_c'
                elif 'solar illumination' in column_lower:
                    fallback_rename[column] = 'solar_pct'
                elif column_lower.startswith('humidity'):
                    fallback_rename[column] = 'humidity_pct'
                elif column_lower.startswith('pressure'):
                    fallback_rename[column] = 'pressure_pa'
                elif column_lower.startswith('radiation'):
                    fallback_rename[column] = 'cosmic_rad_usv_h'
                elif column_lower.startswith('location'):
                    fallback_rename[column] = 'location'
            if fallback_rename:
                df = df.rename(columns=fallback_rename).copy()

        if 'pressure_hpa' not in df.columns:
            if 'pressure_pa' in df.columns:
                df['pressure_hpa'] = pd.to_numeric(df['pressure_pa'], errors='coerce') / 100.0
            else:
                df['pressure_hpa'] = 0.0

        if 'abs_470nm' not in df.columns:
            solar = _series_or_default('solar_pct').fillna(0)
            rad = _series_or_default('cosmic_rad_usv_h').fillna(0)
            df['abs_470nm'] = np.clip((solar / 100.0) * 0.004 + (rad / 50000.0), 0.0, 0.01)

        if 'abs_850nm' not in df.columns:
            df['abs_850nm'] = np.clip(pd.to_numeric(df['abs_470nm'], errors='coerce').fillna(0) * 0.72, 0.0, 0.01)

        if 'scattering_m1' not in df.columns:
            solar = _series_or_default('solar_pct').fillna(0)
            df['scattering_m1'] = np.clip(
                pd.to_numeric(df['abs_470nm'], errors='coerce').fillna(0) * 0.30 +
                (100.0 - solar).clip(lower=0) * 0.00008,
                0.0,
                0.03,
            )

        if 'pm25_ug_m3' not in df.columns:
            regolith_5 = _series_or_default('regolith_5cm_c').fillna(0)
            regolith_50 = _series_or_default('regolith_50cm_c').fillna(0)
            solar = _series_or_default('solar_pct').fillna(0)
            df['pm25_ug_m3'] = np.clip(
                np.abs(regolith_5 - regolith_50) * 0.08 + (100.0 - solar).clip(lower=0) * 0.05,
                0.0,
                20.0,
            )

        if 'ec_ms_cm' not in df.columns:
            df['ec_ms_cm'] = np.clip(0.001 + pd.to_numeric(df['pm25_ug_m3'], errors='coerce').fillna(0) * 0.0006, 0.0, 0.05)

        if 'gps_lat' not in df.columns:
            df['gps_lat'] = -53.0
        if 'gps_lon' not in df.columns:
            df['gps_lon'] = -169.0

        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce').astype('string').fillna(df['timestamp'].astype(str))

        numeric_cols = [
            'temp_c', 'humidity_pct', 'pressure_pa', 'pressure_hpa', 'abs_470nm',
            'abs_850nm', 'scattering_m1', 'pm25_ug_m3', 'cosmic_rad_usv_h',
            'ec_ms_cm', 'gps_lat', 'gps_lon',
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    @staticmethod
    def _load(sensor_type):
        """Generic CSV loader — returns raw DataFrame or None."""
        spec = SensorDataLoader.SENSOR_SPECS.get(sensor_type)
        if not spec:
            return None
        files = spec.get('files')
        if files is None:
            file_value = spec.get('file')
            files = [file_value] if isinstance(file_value, str) else list(file_value or [])
        return SensorDataLoader._load_first_available(files, sheet_name=spec.get('sheet_name', 0))

    @staticmethod
    def load_radar_data():
        """Load RADAR observations."""
        file_path = SensorDataLoader.DATA_DIR / 'mock_radar_observations_1hour.csv'
        if not file_path.exists():
            return None

        df = pd.read_csv(file_path)
        return {
            'sensor': 'radar',
            'name': SensorDataLoader.SENSOR_SPECS['radar']['name'],
            'data': df,
            'summary': SensorDataLoader._analyze_radar(df),
        }

    @staticmethod
    def load_thermal_data():
        """Load THERMAL camera observations."""
        file_path = SensorDataLoader.DATA_DIR / 'mock_thermal_observations_1hour.csv'
        if not file_path.exists():
            return None

        df = pd.read_csv(file_path)
        return {
            'sensor': 'thermal',
            'name': SensorDataLoader.SENSOR_SPECS['thermal']['name'],
            'data': df,
            'summary': SensorDataLoader._analyze_thermal(df),
        }

    @staticmethod
    def load_lidar_data():
        """Load LIDAR observations."""
        file_path = SensorDataLoader.DATA_DIR / 'mock_lidar_observations_1hour.csv'
        if not file_path.exists():
            return None

        df = pd.read_csv(file_path)
        return {
            'sensor': 'lidar',
            'name': SensorDataLoader.SENSOR_SPECS['lidar']['name'],
            'data': df,
            'summary': SensorDataLoader._analyze_lidar(df),
        }

    @staticmethod
    def _analyze_radar(df):
        """Analyze RADAR data."""
        return {
            'total_observations': len(df),
            'unique_objects': df['track_id'].nunique(),
            'object_classes': df['object_class'].value_counts().to_dict(),
            'avg_confidence': float(df['confidence'].mean()),
            'max_range': float(df['range_m'].max()),
            'max_velocity': float(df['radial_velocity_mps'].abs().max()),
            'avg_snr': float(df['snr_db'].mean()),
        }

    @staticmethod
    def _analyze_thermal(df):
        """Analyze THERMAL data."""
        return {
            'total_observations': len(df),
            'unique_objects': df['track_id'].nunique(),
            'object_classes': df['object_class'].value_counts().to_dict(),
            'avg_confidence': float(df['confidence'].mean()),
            'temp_range': {
                'min': float(df['surface_temp_c'].min()),
                'max': float(df['surface_temp_c'].max()),
                'mean': float(df['surface_temp_c'].mean()),
            },
            'thermal_contrast_range': {
                'min': float(df['thermal_contrast_c'].min()),
                'max': float(df['thermal_contrast_c'].max()),
                'mean': float(df['thermal_contrast_c'].mean()),
            },
            'avg_emissivity': float(df['emissivity_estimate'].mean()),
        }

    @staticmethod
    def _analyze_lidar(df):
        """Analyze LIDAR data."""
        distances = np.sqrt(df['x_m']**2 + df['y_m']**2 + df['z_m']**2)
        return {
            'total_observations': len(df),
            'unique_objects': df['track_id'].nunique(),
            'object_classes': df['object_class'].value_counts().to_dict(),
            'avg_confidence': float(df['confidence'].mean()),
            'spatial_range': {
                'x_range': [float(df['x_m'].min()), float(df['x_m'].max())],
                'y_range': [float(df['y_m'].min()), float(df['y_m'].max())],
                'z_range': [float(df['z_m'].min()), float(df['z_m'].max())],
            },
            'max_distance': float(distances.max()),
            'avg_point_count': float(df['point_count'].mean()),
            'avg_intensity': float(df['mean_intensity'].mean()),
        }

    @staticmethod
    def get_sensor_info(sensor_type):
        """Get specifications for a sensor."""
        return SensorDataLoader.SENSOR_SPECS.get(sensor_type)

    @staticmethod
    def get_all_sensors():
        """Get list of all available sensors."""
        return list(SensorDataLoader.SENSOR_SPECS.keys())

    @staticmethod
    def perform_analysis(sensor_type, analysis_type):
        """Perform specific analysis on sensor data."""

        if sensor_type == 'radar':
            data = SensorDataLoader.load_radar_data()
            if not data:
                return {'error': 'RADAR data not found'}
            return SensorDataLoader._analyze_radar_function(data['data'], analysis_type)

        elif sensor_type == 'thermal':
            data = SensorDataLoader.load_thermal_data()
            if not data:
                return {'error': 'THERMAL data not found'}
            return SensorDataLoader._analyze_thermal_function(data['data'], analysis_type)

        elif sensor_type == 'lidar':
            data = SensorDataLoader.load_lidar_data()
            if not data:
                return {'error': 'LIDAR data not found'}
            return SensorDataLoader._analyze_lidar_function(data['data'], analysis_type)

        # New sensors
        new_loaders = {
            'env_probe':  SensorDataLoader.load_env_probe_data,
            'xrd':        SensorDataLoader.load_xrd_data,
            'xrf':        SensorDataLoader.load_xrf_data,
            'gpr':        SensorDataLoader.load_gpr_data,
            'ph':         SensorDataLoader.load_ph_data,
            'soil_core':  SensorDataLoader.load_soil_core_data,
            'gas':        SensorDataLoader.load_gas_data,
        }
        new_analyzers = {
            'env_probe':  SensorDataLoader._analyze_env_probe,
            'xrd':        SensorDataLoader._analyze_xrd,
            'xrf':        SensorDataLoader._analyze_xrf,
            'gpr':        SensorDataLoader._analyze_gpr,
            'ph':         SensorDataLoader._analyze_ph,
            'soil_core':  SensorDataLoader._analyze_soil_core,
            'gas':        SensorDataLoader._analyze_gas,
        }
        if sensor_type in new_loaders:
            data = new_loaders[sensor_type]()
            if not data:
                return {'error': f'{sensor_type} data not found'}
            return new_analyzers[sensor_type](data['data'], analysis_type)

        return {'error': 'Unknown sensor type'}

    @staticmethod
    def _analyze_radar_function(df, analysis_type):
        """Perform RADAR-specific analyses."""

        if analysis_type == 'motion_detection':
            # Find moving objects
            moving = df[df['radial_velocity_mps'].abs() > 0]
            return {
                'analysis': 'Motion Detection',
                'moving_objects': len(moving),
                'total_objects': len(df),
                'avg_velocity': float(moving['radial_velocity_mps'].mean()),
                'max_velocity': float(moving['radial_velocity_mps'].abs().max()),
                'result': f"Detected {len(moving)} moving objects out of {len(df)} total"
            }

        elif analysis_type == 'object_classification':
            # Classify objects by type
            classes = df['object_class'].value_counts().to_dict()
            high_confidence = df[df['confidence'] > 0.8]
            return {
                'analysis': 'Object Classification',
                'classifications': classes,
                'high_confidence_count': len(high_confidence),
                'avg_confidence': float(df['confidence'].mean()),
                'result': f"Found {len(classes)} object types with {len(high_confidence)} high-confidence detections"
            }

        elif analysis_type == 'threat_assessment':
            # Assess threats based on approach velocity
            approaching = df[df['radial_velocity_mps'] > 5]
            threats = approaching[approaching['confidence'] > 0.7]
            return {
                'analysis': 'Threat Assessment',
                'approaching_objects': len(approaching),
                'threat_level_high': len(threats),
                'avg_approach_speed': float(approaching['radial_velocity_mps'].mean()) if len(approaching) > 0 else 0,
                'result': f"Alert: {len(threats)} potential threats approaching at high speed"
            }

        elif analysis_type == 'range_analysis':
            # Analyze object ranges
            return {
                'analysis': 'Range Analysis',
                'min_range': float(df['range_m'].min()),
                'max_range': float(df['range_m'].max()),
                'avg_range': float(df['range_m'].mean()),
                'objects_near': len(df[df['range_m'] < 30]),
                'objects_far': len(df[df['range_m'] > 80]),
                'result': f"Objects detected from {df['range_m'].min():.1f}m to {df['range_m'].max():.1f}m"
            }

        return {'error': f'Unknown analysis type: {analysis_type}'}

    @staticmethod
    def _analyze_thermal_function(df, analysis_type):
        """Perform THERMAL-specific analyses."""

        if analysis_type == 'night_navigation':
            # Evaluate night navigation capability
            warm_objects = df[df['thermal_contrast_c'] > 10]
            visible = df[df['confidence'] > 0.7]
            return {
                'analysis': 'Night Navigation',
                'warm_objects': len(warm_objects),
                'visible_objects': len(visible),
                'avg_thermal_contrast': float(df['thermal_contrast_c'].mean()),
                'night_visibility': f"{len(visible)/len(df)*100:.1f}%",
                'result': f"Night vision enabled: {len(visible)} objects clearly visible"
            }

        elif analysis_type == 'heat_signature':
            # Find heat signatures
            high_temp = df[df['surface_temp_c'] > df['surface_temp_c'].quantile(0.75)]
            organisms = df[df['object_class'].isin(['person', 'animal'])]
            return {
                'analysis': 'Heat Signature Detection',
                'high_temp_objects': len(high_temp),
                'living_organisms': len(organisms),
                'max_temperature': float(df['surface_temp_c'].max()),
                'organism_temp_avg': float(organisms['surface_temp_c'].mean()) if len(organisms) > 0 else 0,
                'result': f"Found {len(organisms)} organisms with avg temp {organisms['surface_temp_c'].mean():.1f}°C"
            }

        elif analysis_type == 'thermal_anomalies':
            # Detect thermal anomalies
            mean_temp = df['surface_temp_c'].mean()
            std_temp = df['surface_temp_c'].std()
            anomalies = df[df['surface_temp_c'] > mean_temp + 2*std_temp]
            return {
                'analysis': 'Thermal Anomaly Detection',
                'anomalies_found': len(anomalies),
                'mean_temp': float(mean_temp),
                'hottest_anomaly': float(anomalies['surface_temp_c'].max()) if len(anomalies) > 0 else 0,
                'anomaly_locations': len(anomalies),
                'result': f"Detected {len(anomalies)} thermal anomalies ({mean_temp:.1f}°C ± {std_temp:.1f}°C baseline)"
            }

        elif analysis_type == 'occlusion_detection':
            # Analyze occlusion levels
            occluded = df[df['occlusion'] != 'none']
            return {
                'analysis': 'Occlusion Detection',
                'total_objects': len(df),
                'occluded_objects': len(occluded),
                'occlusion_types': df['occlusion'].value_counts().to_dict(),
                'visibility': f"{(1 - len(occluded)/len(df))*100:.1f}%",
                'result': f"Visibility: {len(df) - len(occluded)}/{len(df)} objects unoccluded"
            }

        return {'error': f'Unknown analysis type: {analysis_type}'}

    @staticmethod
    def _analyze_lidar_function(df, analysis_type):
        """Perform LIDAR-specific analyses."""

        if analysis_type == '3d_mapping':
            # 3D terrain mapping capability
            return {
                'analysis': '3D Terrain Mapping',
                'x_coverage': f"{df['x_m'].min():.1f}m to {df['x_m'].max():.1f}m",
                'y_coverage': f"{df['y_m'].min():.1f}m to {df['y_m'].max():.1f}m",
                'z_coverage': f"{df['z_m'].min():.1f}m to {df['z_m'].max():.1f}m",
                'total_points': int(df['point_count'].sum()),
                'spatial_resolution': f"avg {df['point_count'].mean():.0f} points per object",
                'result': f"3D map created covering {df['x_m'].max() - df['x_m'].min():.1f}m x {df['y_m'].max() - df['y_m'].min():.1f}m area"
            }

        elif analysis_type == 'obstacle_detection':
            # Obstacle avoidance analysis
            obstacles = df[df['object_class'].isin(['vehicle', 'bicycle', 'unknown'])]
            nearby = df[np.sqrt(df['x_m']**2 + df['y_m']**2) < 30]
            return {
                'analysis': 'Obstacle Detection',
                'obstacles_detected': len(obstacles),
                'nearby_obstacles': len(nearby),
                'avg_obstacle_size': float(df['bbox_length_m'].mean()),
                'largest_obstacle': float(df[df['bbox_length_m'] == df['bbox_length_m'].max()]['bbox_length_m'].iloc[0]),
                'result': f"Detected {len(obstacles)} obstacles; {len(nearby)} within 30m - safe navigation available"
            }

        elif analysis_type == 'path_planning':
            # Evaluate path planning feasibility
            clear_space = df[df['point_count'] < df['point_count'].quantile(0.25)]
            return {
                'analysis': 'Path Planning',
                'sparse_areas': len(clear_space),
                'dense_areas': len(df) - len(clear_space),
                'max_clear_path': float(clear_space['distance_m'].max()) if len(clear_space) > 0 else 0,
                'navigation_confidence': float(df['confidence'].mean()),
                'result': f"Optimal paths identified with {float(df['confidence'].mean())*100:.1f}% confidence"
            }

        elif analysis_type == 'slam':
            # SLAM (Simultaneous Localization and Mapping)
            high_confidence = df[df['confidence'] > 0.7]
            return {
                'analysis': 'SLAM Capability',
                'trackable_features': len(high_confidence),
                'tracking_confidence': float(high_confidence['confidence'].mean()),
                'coverage_points': int(high_confidence['point_count'].sum()),
                'localization_quality': 'High' if len(high_confidence) > len(df)*0.7 else 'Medium',
                'result': f"SLAM ready with {len(high_confidence)} trackable features"
            }

        return {'error': f'Unknown analysis type: {analysis_type}'}

    # ── New sensor loaders ────────────────────────────────────────────────

    @staticmethod
    def load_env_probe_data():
        df = SensorDataLoader._load('env_probe')
        if df is None:
            return None
        df = SensorDataLoader._normalize_env_probe(df)
        return {
            'sensor': 'env_probe',
            'name': SensorDataLoader.SENSOR_SPECS['env_probe']['name'],
            'data': df,
            'summary': {
                'total_observations': len(df),
                'temp_range': {'min': float(df['temp_c'].min()), 'max': float(df['temp_c'].max()), 'mean': float(df['temp_c'].mean())},
                'humidity_range': {'min': float(df['humidity_pct'].min()), 'max': float(df['humidity_pct'].max())},
                'pressure_range': {'min': float(df['pressure_hpa'].min()), 'max': float(df['pressure_hpa'].max())},
                'radiation_mean': float(df['cosmic_rad_usv_h'].mean()),
                'radiation_max': float(df['cosmic_rad_usv_h'].max()),
                'ec_mean': float(df['ec_ms_cm'].mean()),
                'pm25_mean': float(df['pm25_ug_m3'].mean()),
                'solar_mean': float(pd.to_numeric(df['solar_pct'], errors='coerce').fillna(0).mean()) if 'solar_pct' in df.columns else 0.0,
            }
        }

    @staticmethod
    def load_xrd_data():
        df = SensorDataLoader._load('xrd')
        if df is None:
            return None
        return {
            'sensor': 'xrd', 'name': SensorDataLoader.SENSOR_SPECS['xrd']['name'],
            'data': df,
            'summary': {
                'total_scans': len(df),
                'minerals_found': df['primary_mineral'].value_counts().to_dict(),
                'avg_crystallinity': float(df['crystallinity_index'].mean()),
                'avg_amorphous_pct': float(df['amorphous_pct'].mean()),
                'avg_confidence': float(df['confidence'].mean()),
            }
        }

    @staticmethod
    def load_xrf_data():
        df = SensorDataLoader._load('xrf')
        if df is None:
            return None
        return {
            'sensor': 'xrf', 'name': SensorDataLoader.SENSOR_SPECS['xrf']['name'],
            'data': df,
            'summary': {
                'total_scans': len(df),
                'avg_Si_pct': float(df['Si_wt_pct'].mean()),
                'avg_Fe_pct': float(df['Fe_wt_pct'].mean()),
                'avg_Al_pct': float(df['Al_wt_pct'].mean()),
                'avg_confidence': float(df['confidence'].mean()),
                'trace_elements': {'Cr_ppm': float(df['Cr_ppm'].mean()), 'Ni_ppm': float(df['Ni_ppm'].mean())},
            }
        }

    @staticmethod
    def load_gpr_data():
        df = SensorDataLoader._load('gpr')
        if df is None:
            return None
        features = df[df['feature_detected'] != 'none']
        return {
            'sensor': 'gpr', 'name': SensorDataLoader.SENSOR_SPECS['gpr']['name'],
            'data': df,
            'summary': {
                'total_profiles': len(df),
                'features_detected': len(features),
                'feature_types': df['feature_detected'].value_counts().to_dict(),
                'avg_max_depth_m': float(df['max_depth_m'].mean()),
                'avg_confidence': float(df['confidence'].mean()),
            }
        }

    @staticmethod
    def load_ph_data():
        df = SensorDataLoader._load('ph')
        if df is None:
            return None
        return {
            'sensor': 'ph', 'name': SensorDataLoader.SENSOR_SPECS['ph']['name'],
            'data': df,
            'summary': {
                'total_readings': len(df),
                'ph_range': {'min': float(df['ph_value'].min()), 'max': float(df['ph_value'].max()), 'mean': float(df['ph_value'].mean())},
                'avg_orp_mv': float(df['oxidation_reduction_potential_mv'].mean()),
                'avg_confidence': float(df['confidence'].mean()),
            }
        }

    @staticmethod
    def load_soil_core_data():
        df = SensorDataLoader._load('soil_core')
        if df is None:
            return None
        return {
            'sensor': 'soil_core', 'name': SensorDataLoader.SENSOR_SPECS['soil_core']['name'],
            'data': df,
            'summary': {
                'total_samples': len(df),
                'cores': int(df['core_id'].nunique()),
                'avg_bulk_density': float(df['bulk_density_g_cm3'].mean()),
                'avg_moisture': float(df['moisture_percent'].mean()),
                'quality_types': df['sample_quality'].value_counts().to_dict(),
                'volatile_ratio': float((df['volatile_flag'].astype(str).str.lower() != 'none').mean()),
                'good_quality_ratio': float((df['sample_quality'].astype(str).str.lower() == 'good').mean()),
                'avg_cohesion': float(df['cohesion_kpa'].mean()),
                'avg_rock_fragment_pct': float(df['rock_fragment_percent'].mean()),
                'avg_confidence': float(df['confidence'].mean()),
            }
        }

    @staticmethod
    def load_gas_data():
        df = SensorDataLoader._load('gas')
        if df is None:
            return None
        return {
            'sensor': 'gas', 'name': SensorDataLoader.SENSOR_SPECS['gas']['name'],
            'data': df,
            'summary': {
                'total_samples': len(df),
                'sources': df['sample_source'].value_counts().to_dict(),
                'avg_CO2_ppm': float(df['CO2_ppm'].mean()),
                'avg_CH4_ppb': float(df['CH4_ppb'].mean()),
                'avg_total_voc': float(df['total_voc_ppb'].mean()),
                'avg_confidence': float(df['confidence'].mean()),
            }
        }

    # ── New sensor analyses ───────────────────────────────────────────────

    @staticmethod
    def _analyze_env_probe(df, analysis_type):
        if analysis_type == 'atmospheric_profiling':
            return {
                'analysis': 'Atmospheric Profiling',
                'temp_mean': float(df['temp_c'].mean()), 'temp_max': float(df['temp_c'].max()),
                'humidity_mean': float(df['humidity_pct'].mean()),
                'pressure_mean': float(df['pressure_hpa'].mean()),
                'pressure_delta': float(df['pressure_hpa'].max() - df['pressure_hpa'].min()),
                'result': f"Temp {df['temp_c'].mean():.1f}C, Humidity {df['humidity_pct'].mean():.1f}%, Pressure {df['pressure_hpa'].mean():.0f} hPa",
            }
        elif analysis_type == 'air_quality_analysis':
            high_scatter = df[df['scattering_m1'] > df['scattering_m1'].quantile(0.8)]
            return {
                'analysis': 'Air Quality Analysis',
                'avg_absorbance_470nm': float(df['abs_470nm'].mean()),
                'avg_absorbance_850nm': float(df['abs_850nm'].mean()),
                'avg_scattering': float(df['scattering_m1'].mean()),
                'avg_pm25': float(df['pm25_ug_m3'].mean()),
                'high_particulate_events': len(high_scatter),
                'result': f"PM2.5 avg {df['pm25_ug_m3'].mean():.1f} ug/m3; {len(high_scatter)} high-scattering events",
            }
        elif analysis_type == 'cosmic_radiation_monitoring':
            high_rad = df[df['cosmic_rad_usv_h'] > df['cosmic_rad_usv_h'].quantile(0.9)]
            return {
                'analysis': 'Cosmic Radiation Monitoring',
                'avg_dose': float(df['cosmic_rad_usv_h'].mean()),
                'max_dose': float(df['cosmic_rad_usv_h'].max()),
                'high_radiation_periods': len(high_rad),
                'cumulative_dose_usv': float(df['cosmic_rad_usv_h'].sum() * (2 / 3600)),
                'result': f"Avg dose {df['cosmic_rad_usv_h'].mean():.4f} uSv/h; {len(high_rad)} elevated-radiation periods",
            }
        elif analysis_type == 'electrical_conductivity_survey':
            high_ec = df[df['ec_ms_cm'] > 1.2]
            return {
                'analysis': 'Electrical Conductivity Survey',
                'avg_ec': float(df['ec_ms_cm'].mean()),
                'max_ec': float(df['ec_ms_cm'].max()),
                'high_ec_zones': len(high_ec),
                'ec_trend': 'increasing' if df['ec_ms_cm'].iloc[-100:].mean() > df['ec_ms_cm'].iloc[:100].mean() else 'stable',
                'result': f"EC avg {df['ec_ms_cm'].mean():.3f} mS/cm; {len(high_ec)} high-conductivity zones",
            }
        elif analysis_type == 'dust_particulate_monitoring':
            dusty = df[df['pm25_ug_m3'] > 15]
            return {
                'analysis': 'Dust & Particulate Monitoring',
                'avg_pm25': float(df['pm25_ug_m3'].mean()),
                'max_pm25': float(df['pm25_ug_m3'].max()),
                'dusty_periods': len(dusty),
                'dust_pct_time': round(len(dusty) / len(df) * 100, 1),
                'result': f"PM2.5 avg {df['pm25_ug_m3'].mean():.1f} ug/m3; dusty {len(dusty)/len(df)*100:.1f}% of traverse",
            }
        return {'error': f'Unknown analysis: {analysis_type}'}

    @staticmethod
    def _analyze_xrd(df, analysis_type):
        if analysis_type == 'mineral_phase_identification':
            top = df['primary_mineral'].value_counts().head(5).to_dict()
            dominant = df['primary_mineral'].mode()[0]
            return {
                'analysis': 'Mineral Phase Identification',
                'dominant_mineral': dominant,
                'top_minerals': top,
                'total_scans': len(df),
                'result': f"Dominant mineral: {dominant.upper()} — in {top.get(dominant,0)}/{len(df)} scans",
            }
        elif analysis_type == 'crystallinity_index_measurement':
            hi = df[df['crystallinity_index'] > 0.8]
            return {
                'analysis': 'Crystallinity Index',
                'avg_crystallinity': float(df['crystallinity_index'].mean()),
                'highly_crystalline_samples': len(hi),
                'avg_amorphous_pct': float(df['amorphous_pct'].mean()),
                'result': f"Avg crystallinity {df['crystallinity_index'].mean():.2f}; {df['amorphous_pct'].mean():.1f}% amorphous phase",
            }
        elif analysis_type == 'amorphous_fraction_estimation':
            glass_count = int((df['primary_mineral'] == 'glass_basaltic').sum())
            return {
                'analysis': 'Amorphous Fraction Estimation',
                'avg_amorphous_pct': float(df['amorphous_pct'].mean()),
                'max_amorphous_pct': float(df['amorphous_pct'].max()),
                'glass_rich_samples': glass_count,
                'result': f"Mean amorphous {df['amorphous_pct'].mean():.1f}%; impact glass in {glass_count} scans",
            }
        elif analysis_type == 'multi_mineral_composition':
            return {
                'analysis': 'Multi-mineral Composition',
                'avg_primary_pct': float(df['primary_pct'].mean()),
                'avg_secondary_pct': float(df['secondary_pct'].mean()),
                'avg_tertiary_pct': float(df['tertiary_pct'].mean()),
                'unique_primaries': df['primary_mineral'].nunique(),
                'result': f"Avg: {df['primary_pct'].mean():.0f}% primary + {df['secondary_pct'].mean():.0f}% secondary + {df['tertiary_pct'].mean():.0f}% tertiary",
            }
        elif analysis_type == 'crystallographic_peak_analysis':
            return {
                'analysis': 'Crystallographic Peak Analysis',
                'avg_peak_2theta': float(df['peak_2theta_deg'].mean()),
                'avg_d_spacing_A': float(df['d_spacing_angstrom'].mean()),
                'avg_detector_counts': float(df['detector_counts'].mean()),
                'avg_scan_duration_s': float(df['scan_duration_s'].mean()),
                'result': f"Avg 2-theta peak {df['peak_2theta_deg'].mean():.1f} deg, d-spacing {df['d_spacing_angstrom'].mean():.3f} Angstrom",
            }
        return {'error': f'Unknown analysis: {analysis_type}'}

    @staticmethod
    def _analyze_xrf(df, analysis_type):
        if analysis_type == 'major_element_analysis':
            majors = {c: float(df[c].mean()) for c in ['Si_wt_pct','Al_wt_pct','Fe_wt_pct','Ca_wt_pct','Mg_wt_pct']}
            top = max(majors, key=majors.get)
            return {
                'analysis': 'Major Element Analysis',
                'major_elements': majors,
                'dominant_element': top.split('_')[0],
                'result': f"Dominant: {top.split('_')[0]} ({majors[top]:.1f} wt%); basaltic composition",
            }
        elif analysis_type == 'trace_element_detection':
            return {
                'analysis': 'Trace Element Detection',
                'avg_Cr_ppm': float(df['Cr_ppm'].mean()), 'max_Cr_ppm': float(df['Cr_ppm'].max()),
                'avg_Ni_ppm': float(df['Ni_ppm'].mean()),
                'avg_Sr_ppm': float(df['Sr_ppm'].mean()),
                'avg_Zr_ppm': float(df['Zr_ppm'].mean()),
                'result': f"Cr avg {df['Cr_ppm'].mean():.0f} ppm, Ni {df['Ni_ppm'].mean():.0f} ppm",
            }
        elif analysis_type == 'geochemical_classification':
            si = float(df['Si_wt_pct'].mean())
            rock = 'basalt' if si < 52 else 'andesite' if si < 63 else 'rhyolite'
            mg_num = round(float(df['Mg_wt_pct'].mean() / (df['Mg_wt_pct'].mean() + df['Fe_wt_pct'].mean())) * 100, 1)
            return {
                'analysis': 'Geochemical Classification',
                'avg_SiO2': si, 'avg_FeO': float(df['Fe_wt_pct'].mean()),
                'rock_type': rock, 'mg_number': mg_num,
                'result': f"Classification: {rock.upper()} (SiO2={si:.1f} wt%, Mg#={mg_num})",
            }
        elif analysis_type == 'regolith_maturity_index':
            mat = float((df['Fe_wt_pct'] / df['Ti_wt_pct']).mean())
            return {
                'analysis': 'Regolith Maturity Index',
                'fe_ti_ratio': round(mat, 2),
                'maturity': 'mature' if mat > 4 else 'submature',
                'result': f"Fe/Ti ratio {mat:.2f} => {'mature' if mat>4 else 'submature'} regolith",
            }
        elif analysis_type == 'elemental_ratio_calculation':
            return {
                'analysis': 'Elemental Ratio Calculation',
                'si_al_ratio': round(float(df['Si_wt_pct'].mean() / df['Al_wt_pct'].mean()), 2),
                'ca_al_ratio': round(float(df['Ca_wt_pct'].mean() / df['Al_wt_pct'].mean()), 2),
                'fe_mg_ratio': round(float(df['Fe_wt_pct'].mean() / df['Mg_wt_pct'].mean()), 2),
                'avg_loi': float(df['loi_wt_pct'].mean()),
                'result': f"Si/Al={df['Si_wt_pct'].mean()/df['Al_wt_pct'].mean():.2f}, Ca/Al={df['Ca_wt_pct'].mean()/df['Al_wt_pct'].mean():.2f}",
            }
        return {'error': f'Unknown analysis: {analysis_type}'}

    @staticmethod
    def _analyze_gpr(df, analysis_type):
        if analysis_type == 'lava_tube_detection':
            voids = df[df['feature_detected'] == 'void']
            avg_d = float(pd.to_numeric(voids['feature_depth_m'], errors='coerce').mean()) if len(voids) else 0
            return {
                'analysis': 'Lava Tube / Void Detection',
                'voids_found': len(voids), 'avg_depth_m': round(avg_d, 2), 'total_profiles': len(df),
                'result': f"Found {len(voids)} sub-surface void(s) at avg {avg_d:.1f} m depth",
            }
        elif analysis_type == 'underground_ice_detection':
            ice = df[df['feature_detected'] == 'ice_lens']
            avg_d = float(pd.to_numeric(ice['feature_depth_m'], errors='coerce').mean()) if len(ice) else 0
            return {
                'analysis': 'Underground Ice Detection',
                'ice_lenses_found': len(ice), 'avg_depth_m': round(avg_d, 2),
                'result': f"Detected {len(ice)} ice lens(es) at avg {avg_d:.1f} m" if len(ice) else "No ice lenses in current traverse",
            }
        elif analysis_type == 'stratigraphic_layer_mapping':
            layers = df[df['feature_detected'] == 'rock_layer']
            avg_d = float(pd.to_numeric(layers['feature_depth_m'], errors='coerce').mean()) if len(layers) else 0
            return {
                'analysis': 'Stratigraphic Layer Mapping',
                'layers_found': len(layers), 'avg_layer_depth_m': round(avg_d, 2),
                'avg_max_penetration_m': float(df['max_depth_m'].mean()),
                'result': f"Mapped {len(layers)} stratigraphic boundaries; avg penetration {df['max_depth_m'].mean():.1f} m",
            }
        elif analysis_type == 'fracture_system_identification':
            frac = df[df['feature_detected'] == 'fracture']
            avg_d = float(pd.to_numeric(frac['feature_depth_m'], errors='coerce').mean()) if len(frac) else 0
            return {
                'analysis': 'Fracture System Identification',
                'fractures_found': len(frac), 'avg_depth_m': round(avg_d, 2),
                'result': f"Identified {len(frac)} fracture zone(s)",
            }
        elif analysis_type == 'regolith_depth_profiling':
            return {
                'analysis': 'Regolith Depth Profiling',
                'profiles_analyzed': len(df),
                'avg_max_depth_m': float(df['max_depth_m'].mean()),
                'avg_dielectric_const': float(df['dielectric_constant'].mean()),
                'result': f"Profiled to avg {df['max_depth_m'].mean():.1f} m; dielectric e={df['dielectric_constant'].mean():.2f}",
            }
        return {'error': f'Unknown analysis: {analysis_type}'}

    @staticmethod
    def _analyze_ph(df, analysis_type):
        if analysis_type == 'ph_measurement':
            acidic = df[df['ph_value'] < 7]
            return {
                'analysis': 'pH Measurement',
                'avg_ph': float(df['ph_value'].mean()),
                'min_ph': float(df['ph_value'].min()), 'max_ph': float(df['ph_value'].max()),
                'acidic_samples': len(acidic), 'alkaline_samples': len(df) - len(acidic),
                'result': f"Mean pH {df['ph_value'].mean():.2f} ({'alkaline' if df['ph_value'].mean()>7 else 'acidic'})",
            }
        elif analysis_type == 'oxidation_reduction_potential':
            orp = float(df['oxidation_reduction_potential_mv'].mean())
            return {
                'analysis': 'ORP (Redox Potential)',
                'avg_orp_mv': orp, 'max_orp_mv': float(df['oxidation_reduction_potential_mv'].max()),
                'redox_environment': 'oxidising' if orp > 0 else 'reducing',
                'result': f"ORP avg {orp:.0f} mV => {'oxidising' if orp>0 else 'reducing'} conditions",
            }
        elif analysis_type == 'ionic_strength_estimation':
            return {
                'analysis': 'Ionic Strength Estimation',
                'avg_ionic_strength': float(df['ionic_strength_mol_l'].mean()),
                'avg_buffer_capacity': float(df['buffer_capacity'].mean()),
                'avg_moisture_pct': float(df['moisture_pct'].mean()),
                'result': f"Ionic strength {df['ionic_strength_mol_l'].mean():.4f} mol/L; moisture {df['moisture_pct'].mean():.1f}%",
            }
        elif analysis_type == 'buffer_capacity_analysis':
            hi = df[df['buffer_capacity'] > df['buffer_capacity'].quantile(0.75)]
            return {
                'analysis': 'Buffer Capacity Analysis',
                'avg_buffer': float(df['buffer_capacity'].mean()),
                'high_buffer_zones': len(hi),
                'result': f"Avg buffer capacity {df['buffer_capacity'].mean():.4f}; {len(hi)} high-buffering zones",
            }
        elif analysis_type == 'depth_profile_ph_mapping':
            by_depth = {str(k): round(v, 2) for k, v in df.groupby('sample_depth_cm')['ph_value'].mean().to_dict().items()}
            return {
                'analysis': 'Depth-Profile pH Mapping',
                'ph_by_depth': by_depth,
                'result': f"pH varies across {len(by_depth)} depth levels: " + ", ".join(f"{k}cm={v}" for k, v in by_depth.items()),
            }
        return {'error': f'Unknown analysis: {analysis_type}'}

    @staticmethod
    def _analyze_soil_core(df, analysis_type):
        # FINAL lunar soil-core schema: depth_top_cm, depth_bottom_cm, penetration_force_n,
        # drill_current_a, rotation_speed_rpm, regolith_temp_c, bulk_density_g_cm3,
        # sample_mass_g, grain_size_median_um, cohesion_kpa, moisture_percent,
        # volatile_flag, rock_fragment_percent, sample_quality, confidence
        if analysis_type == 'bulk_density_measurement':
            hi = df[df['bulk_density_g_cm3'] > 1.7]
            return {
                'analysis': 'Bulk Density Measurement',
                'avg_bulk_density_g_cm3': round(float(df['bulk_density_g_cm3'].mean()), 3),
                'max_bulk_density_g_cm3': round(float(df['bulk_density_g_cm3'].max()), 3),
                'min_bulk_density_g_cm3': round(float(df['bulk_density_g_cm3'].min()), 3),
                'compacted_samples': int(len(hi)),
                'result': f"Avg {df['bulk_density_g_cm3'].mean():.3f} g/cm³; {len(hi)} compacted samples (>1.7)",
            }
        elif analysis_type == 'porosity_moisture_content':
            # Lunar regolith grain density ~2.9 g/cm³; porosity = 1 - bulk/grain
            porosity = (1 - df['bulk_density_g_cm3'] / 2.9) * 100
            return {
                'analysis': 'Porosity & Moisture Content',
                'avg_porosity_pct': round(float(porosity.mean()), 1),
                'avg_moisture_pct': round(float(df['moisture_percent'].mean()), 3),
                'max_moisture_pct': round(float(df['moisture_percent'].max()), 3),
                'result': f"Porosity {porosity.mean():.1f}% (derived); moisture {df['moisture_percent'].mean():.2f}%",
            }
        elif analysis_type == 'volatile_detection':
            vol = df[df['volatile_flag'] != 'none']
            damp = df[df['moisture_percent'] > df['moisture_percent'].quantile(0.9)]
            return {
                'analysis': 'Volatile Detection',
                'volatile_bearing_samples': int(len(vol)),
                'volatile_flag_breakdown': df['volatile_flag'].value_counts().to_dict(),
                'avg_moisture_pct': round(float(df['moisture_percent'].mean()), 3),
                'high_moisture_samples': int(len(damp)),
                'result': f"{len(vol)} samples flagged for trapped volatiles; {len(damp)} high-moisture pockets",
            }
        elif analysis_type == 'texture_compaction_analysis':
            return {
                'analysis': 'Texture & Drillability Analysis',
                'avg_grain_size_um': round(float(df['grain_size_median_um'].mean()), 1),
                'avg_cohesion_kpa': round(float(df['cohesion_kpa'].mean()), 3),
                'avg_penetration_force_n': round(float(df['penetration_force_n'].mean()), 1),
                'avg_drill_current_a': round(float(df['drill_current_a'].mean()), 3),
                'avg_rock_fragment_pct': round(float(df['rock_fragment_percent'].mean()), 1),
                'sample_quality': df['sample_quality'].value_counts().to_dict(),
                'result': f"Median grain {df['grain_size_median_um'].mean():.0f} µm; avg drill force {df['penetration_force_n'].mean():.0f} N",
            }
        elif analysis_type == 'stratigraphic_layering':
            by_depth = {f"{int(k[0])}-{int(k[1])}cm": round(float(v), 3)
                        for k, v in df.groupby(['depth_top_cm', 'depth_bottom_cm'])['bulk_density_g_cm3'].mean().items()}
            return {
                'analysis': 'Stratigraphic Layering (0-15 cm)',
                'samples': int(len(df)),
                'cores': int(df['core_id'].nunique()),
                'depth_intervals': len(by_depth),
                'density_by_layer': by_depth,
                'result': f"{df['core_id'].nunique()} cores, {len(df)} samples across {len(by_depth)} depth intervals",
            }
        return {'error': f'Unknown analysis: {analysis_type}'}

    @staticmethod
    def _analyze_gas(df, analysis_type):
        atm  = df[df['sample_source'] == 'atmosphere']
        soil = df[df['sample_source'] != 'atmosphere']
        if analysis_type == 'atmospheric_gas_composition':
            return {
                'analysis': 'Atmospheric Gas Composition',
                'avg_N2_pct': float(atm['N2_pct'].mean()) if len(atm) else 0,
                'avg_O2_pct': float(atm['O2_pct'].mean()) if len(atm) else 0,
                'avg_CO2_ppm': float(atm['CO2_ppm'].mean()) if len(atm) else 0,
                'avg_Ar_pct': float(atm['Ar_pct'].mean()) if len(atm) else 0,
                'samples_collected': len(atm),
                'result': f"Atm: N2={atm['N2_pct'].mean():.1f}%, O2={atm['O2_pct'].mean():.1f}%, CO2={atm['CO2_ppm'].mean():.0f} ppm" if len(atm) else "No atmospheric samples",
            }
        elif analysis_type == 'trace_gas_detection':
            hi_ch4 = df[df['CH4_ppb'] > 3000]
            return {
                'analysis': 'Trace Gas Detection',
                'avg_CH4_ppb': float(df['CH4_ppb'].mean()),
                'avg_H2S_ppb': float(df['H2S_ppb'].mean()),
                'avg_SO2_ppb': float(df['SO2_ppb'].mean()),
                'avg_N2O_ppb': float(df['N2O_ppb'].mean()),
                'elevated_methane_samples': len(hi_ch4),
                'result': f"CH4 avg {df['CH4_ppb'].mean():.0f} ppb; {len(hi_ch4)} elevated-methane samples",
            }
        elif analysis_type == 'soil_respiration_measurement':
            s_co2 = float(soil['CO2_ppm'].mean()) if len(soil) else 0
            a_co2 = float(atm['CO2_ppm'].mean()) if len(atm) else 415
            return {
                'analysis': 'Soil Respiration Measurement',
                'soil_CO2_ppm': round(s_co2, 1), 'atm_CO2_ppm': round(a_co2, 1),
                'ratio': round(s_co2 / a_co2, 2) if a_co2 else 0,
                'result': f"Soil CO2 {s_co2:.0f} ppm vs atm {a_co2:.0f} ppm (ratio {s_co2/a_co2:.1f}x)",
            }
        elif analysis_type == 'voc_profiling':
            hi = df[df['total_voc_ppb'] > 100]
            return {
                'analysis': 'VOC Profiling',
                'avg_voc_ppb': float(df['total_voc_ppb'].mean()),
                'max_voc_ppb': float(df['total_voc_ppb'].max()),
                'elevated_voc_samples': len(hi),
                'soil_avg_voc': float(soil['total_voc_ppb'].mean()) if len(soil) else 0,
                'result': f"VOC avg {df['total_voc_ppb'].mean():.0f} ppb; {len(hi)} samples above 100 ppb threshold",
            }
        elif analysis_type == 'gas_source_comparison':
            s_ch4 = float(soil['CH4_ppb'].mean()) if len(soil) else 0
            a_ch4 = float(atm['CH4_ppb'].mean()) if len(atm) else 0
            return {
                'analysis': 'Gas Source Comparison',
                'atm_CH4_ppb': round(a_ch4, 1), 'soil_CH4_ppb': round(s_ch4, 1),
                'atm_CO2_ppm': round(float(atm['CO2_ppm'].mean()), 1) if len(atm) else 0,
                'soil_CO2_ppm': round(float(soil['CO2_ppm'].mean()), 1) if len(soil) else 0,
                'sources_sampled': df['sample_source'].value_counts().to_dict(),
                'result': f"Soil CH4 {s_ch4:.0f} vs atm {a_ch4:.0f} ppb — soil enrichment {s_ch4/a_ch4:.1f}x" if a_ch4 else "Insufficient data",
            }
        return {'error': f'Unknown analysis: {analysis_type}'}
