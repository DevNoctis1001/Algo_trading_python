from datetime import datetime, timedelta

from assets.assets_provider import AssetsProvider
from entities.timespan import TimeSpan
from pipeline.processor import Processor
from pipeline.processors.candle_cache import CandleCache
from pipeline.processors.mongodb_sink import MongoDBSinkProcessor
from pipeline.processors.returns import ReturnsCalculatorProcessor
from pipeline.processors.technicals import TechnicalsProcessor
from pipeline.processors.technicals_normalizer import TechnicalsNormalizerProcessor
from pipeline.reverse_source import ReverseSource
from pipeline.runner import PipelineRunner
from pipeline.source import Source
from pipeline.sources.ib_history import IBHistorySource
from pipeline.sources.mongodb_source import MongoDBSource
from pipeline.terminators.technicals_binner import TechnicalsBinner
from providers.ib.interactive_brokers_connector import InteractiveBrokersConnector
from storage.mongodb_storage import MongoDBStorage


class LoadersPipelines:
    @staticmethod
    def build_daily_loader() -> PipelineRunner:
        mongodb_storage = MongoDBStorage()

        from_time = datetime.now() - timedelta(days=365 * 3)
        symbols = AssetsProvider.get_sp500_symbols()

        source = IBHistorySource(InteractiveBrokersConnector(), symbols, TimeSpan.Day, from_time)

        sink = MongoDBSinkProcessor(mongodb_storage)
        cache_processor = CandleCache(sink)
        processor = TechnicalsProcessor(cache_processor)

        return PipelineRunner(source, processor)

    @staticmethod
    def build_returns_calculator() -> PipelineRunner:
        mongodb_storage = MongoDBStorage()
        symbols = AssetsProvider.get_sp500_symbols()

        from_time = datetime.now() - timedelta(days=365 * 2)
        source = MongoDBSource(mongodb_storage, symbols, TimeSpan.Day, from_time)
        source = ReverseSource(source)

        sink = MongoDBSinkProcessor(mongodb_storage)
        cache_processor = CandleCache(sink)
        processor = ReturnsCalculatorProcessor(cache_processor)

        return PipelineRunner(source, processor)

    @staticmethod
    def _build_mongo_source(days_back: int) -> Source:
        mongodb_storage = MongoDBStorage()
        symbols = AssetsProvider.get_sp500_symbols()

        from_time = datetime.now() - timedelta(days=days_back)
        source = MongoDBSource(mongodb_storage, symbols, TimeSpan.Day, from_time)
        return source

    @staticmethod
    def _build_technicals_base_processor_chain() -> Processor:
        mongodb_storage = MongoDBStorage()
        sink = MongoDBSinkProcessor(mongodb_storage)
        cache_processor = CandleCache(sink)
        technical_normalizer = TechnicalsNormalizerProcessor(next_processor=cache_processor)
        technicals = TechnicalsProcessor(technical_normalizer)
        return technicals

    @staticmethod
    def build_technicals_calculator() -> PipelineRunner:
        source = LoadersPipelines._build_mongo_source(365)
        technicals = LoadersPipelines._build_technicals_base_processor_chain()
        return PipelineRunner(source, technicals)

    @staticmethod
    def build_technicals_with_buckets_calculator(bins_file_path: str) -> PipelineRunner:
        source = LoadersPipelines._build_mongo_source(365)
        technicals = LoadersPipelines._build_technicals_base_processor_chain()

        symbols = AssetsProvider.get_sp500_symbols()
        technicals_binner = TechnicalsBinner(symbols, bins_file_path)

        return PipelineRunner(source, technicals, technicals_binner)
