from datetime import datetime
from typing import List, Tuple
from unittest import TestCase

from entities.candle import Candle
from entities.strategy_signal import StrategySignal, SignalDirection
from entities.timespan import TimeSpan
from fakes.strategy_executor import FakeStrategyExecutor
from pipeline.processors.candle_cache import CandleCache
from pipeline.processors.strategy import StrategyProcessor
from pipeline.processors.technicals import INDICATORS_ATTACHMENT_KEY, Indicators
from pipeline.shared_context import SharedContext
from pipeline.strategies.simaple_sma import SimpleSMA
from unit import generate_candle, TEST_SYMBOL


class TestSimpleSMAStrategy(TestCase):
    def test_long(self):
        def _check(signals: List[StrategySignal]):
            self.assertEqual(1, len(signals))
            self.assertEqual(TEST_SYMBOL, signals[0].symbol)
            self.assertEqual(SignalDirection.Long, signals[0].direction)

        prev_candle, current_candle = self._get_candles()

        context = SharedContext()
        cache_processor = CandleCache(None)
        cache_processor.process(context, prev_candle)

        processor = StrategyProcessor([SimpleSMA()], FakeStrategyExecutor(_check), None)
        processor.process(context, current_candle)

    def test_short(self):
        def _check(signals: List[StrategySignal]):
            self.assertEqual(1, len(signals))
            self.assertEqual(TEST_SYMBOL, signals[0].symbol)
            self.assertEqual(SignalDirection.Short, signals[0].direction)

        current_candle, prev_candle = self._get_candles()

        context = SharedContext()
        cache_processor = CandleCache(None)
        cache_processor.process(context, prev_candle)

        processor = StrategyProcessor([SimpleSMA()], FakeStrategyExecutor(_check), None)
        processor.process(context, current_candle)

    def _get_candles(self) -> Tuple[Candle, Candle]:
        prev_candle = generate_candle(TimeSpan.Day, datetime.now())
        current_candle = generate_candle(TimeSpan.Day, datetime.now())

        prev_indicators = Indicators()
        prev_indicators.indicators['sma5'] = 5
        prev_indicators.indicators['sma20'] = 6

        current_indicators = Indicators()
        current_indicators.indicators['sma5'] = 6
        current_indicators.indicators['sma20'] = 5

        prev_candle.attachments.add_attachement(INDICATORS_ATTACHMENT_KEY, prev_indicators)
        current_candle.attachments.add_attachement(INDICATORS_ATTACHMENT_KEY, current_indicators)
        return prev_candle, current_candle
