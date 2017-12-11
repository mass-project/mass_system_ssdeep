import sys
import time
import logging
import os
from common_analysis_ssdeep import CommonAnalysisSsdeep
from mass_api_client import ConnectionManager
from mass_api_client.resources import Sample, SampleRelationType
from mass_api_client.utils import process_analyses, get_or_create_analysis_system_instance

logging.basicConfig()
log = logging.getLogger('ssdeep_analysis_system')
log.setLevel(logging.INFO)


class SsdeepAnalysisInstance:
    def __init__(self):
        self.cache = dict()
        self._load_cache()
        self.ssdeep_analysis = CommonAnalysisSsdeep(self.cache)
        self.relation_type = SampleRelationType.get_or_create('ssdeep', directed=False)

    def _load_cache(self):
        log.info('Start loading cache...')
        start_time = time.time()
        for sample in Sample.query(has_file=True):
            self.cache[sample.id] = sample.unique_features.file.ssdeep_hash
        log.info('Finished building cache in {}sec. Size {} bytes.'.format(time.time() - start_time, sys.getsizeof(self.cache)))

    def __call__(self, scheduled_analysis):
        sample = scheduled_analysis.get_sample()
        log.info('Analysing {}'.format(sample))
        report = self.ssdeep_analysis.analyze_string(sample.unique_features.file.ssdeep_hash, sample.id)

        for identifier, value in report['similar samples']:
            self.relation_type.create_relation(sample, Sample.get(identifier), additional_metadata={'match': value})

        scheduled_analysis.create_report(additional_metadata={'number_of_similar_samples': len(report['similar samples'])})


if __name__ == "__main__":
    api_key = os.getenv('MASS_API_KEY', '')
    log.info('Got API KEY {}'.format(api_key))
    server_addr = os.getenv('MASS_SERVER', 'http://localhost:8000/api/')
    log.info('Connecting to {}'.format(server_addr))
    timeout = int(os.getenv('MASS_TIMEOUT', '60'))
    ConnectionManager().register_connection('default', api_key, server_addr, timeout=timeout)

    analysis_system_instance = get_or_create_analysis_system_instance(identifier='ssdeep',
                                                                      verbose_name='ssdeep',
                                                                      tag_filter_exp='sample-type:filesample'
                                                                      )
    process_analyses(analysis_system_instance, SsdeepAnalysisInstance(), sleep_time=7, delete_instance_on_exit=True)
