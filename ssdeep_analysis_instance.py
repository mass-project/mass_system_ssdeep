import sys
import time
import logging
import ssdeep
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
            self.cache[sample.id] = sample.unique_features['file']['ssdeep_hash']
        log.info('Finished building cache in {}sec. Size {} bytes.'.format(time.time() - start_time, sys.getsizeof(self.cache)))

    def __call__(self, scheduled_analysis):
        sample = scheduled_analysis.get_sample()

        similar_samples = []
        for other in Sample.query(has_file=True):
            if sample.id == other.id:
                continue
            match = ssdeep.compare(sample.unique_features['file']['ssdeep_hash'], other.unique_features['file']['ssdeep_hash'])
            if match > 0:
                similar_samples.append((other.id, match))

        for identifier, value in similar_samples:
            self.relation_type.create_relation(sample, Sample.get(identifier), additional_metadata={'match': value})

        scheduled_analysis.create_report(additional_metadata={'number_of_similar_samples': len(similar_samples)})


if __name__ == "__main__":
    ConnectionManager().register_connection('default',
                                            'IjVhMDBlMTYzMTViNzdmMzE2YTlkYThiZiI.6WyegDGWlqOBKcWlozKJt-2_gKM',
                                            'http://localhost:8000/api/')

    analysis_system_instance = get_or_create_analysis_system_instance(identifier='ssdeep',
                                                                      verbose_name='ssdeep',
                                                                      tag_filter_exp='sample-type:filesample'
                                                                      )
    process_analyses(analysis_system_instance, SsdeepAnalysisInstance(), sleep_time=7)
