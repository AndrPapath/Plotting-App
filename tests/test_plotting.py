# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""Every plot mode draws headlessly, and every failure mode is reported."""

import sys as _sys
from pathlib import Path as _Path

# Runnable straight from the editor: make the project root importable.
_ROOT = str(_Path(__file__).resolve().parents[1])
if _ROOT not in _sys.path:
    _sys.path.insert(0, _ROOT)

import unittest

import matplotlib

matplotlib.use("Agg")

import numpy as np
from matplotlib.figure import Figure

import plotting
from plotting import SimpleTrace
from plotting.options import X_AXIS_INDEX, OptionError, Options, PlottingError
from plotting.styling import MAX_TICKS, apply_axes_style


def make_axes():
    figure = Figure(layout="constrained")
    return figure.add_subplot()


def make_traces(n_points=25):
    x = np.linspace(0.5, 10.0, n_points)
    return [
        SimpleTrace("time", x),
        SimpleTrace("1e-06", np.sin(x)),
        SimpleTrace("2e-06", np.cos(x)),
    ]


def options_for(module, **values):
    return Options.from_specs(module.get_option_specs(), values)


class ModeContractTests(unittest.TestCase):
    def test_every_registered_mode_draws_and_refreshes(self):
        traces = make_traces()
        for name in plotting.mode_names():
            with self.subTest(mode=name):
                module = plotting.load_mode(name)
                axes = make_axes()
                options = options_for(module)
                module.draw(axes, traces, options)
                module.refresh(axes, options)
                self.assertTrue(axes.lines or axes.patches)

    def test_unknown_mode_is_rejected(self):
        with self.assertRaises(PlottingError):
            plotting.load_mode("Sankey")

    def test_modules_accept_plain_dicts(self):
        module = plotting.load_mode("XY Plot")
        axes = make_axes()
        module.draw(axes, make_traces(), {"Plot Title": "from a dict"})
        self.assertEqual(axes.get_title(), "from a dict")


class XYPlotTests(unittest.TestCase):
    def setUp(self):
        self.module = plotting.load_mode("XY Plot")
        self.axes = make_axes()

    def test_x_axis_selection_is_honoured(self):
        traces = make_traces()
        options = options_for(self.module, **{X_AXIS_INDEX: 1})
        self.module.draw(self.axes, traces, options)
        # Trace 1 became the X axis, so 'time' and '2e-06' are the curves.
        self.assertEqual([line.get_label() for line in self.axes.lines],
                         ["time", "2e-06"])

    def test_out_of_range_x_index_falls_back_to_the_first_trace(self):
        options = options_for(self.module, **{X_AXIS_INDEX: 99})
        self.module.draw(self.axes, make_traces(), options)
        self.assertEqual(len(self.axes.lines), 2)

    def test_per_trace_scale_is_applied(self):
        traces = make_traces()
        traces[1].scale = 3.0
        self.module.draw(self.axes, traces, options_for(self.module))
        peak = max(self.axes.lines[0].get_ydata())
        self.assertGreater(peak, 2.9)

    def test_empty_and_hidden_inputs_raise_readable_errors(self):
        with self.assertRaises(PlottingError):
            self.module.draw(self.axes, [], options_for(self.module))
        traces = make_traces()
        for trace in traces[1:]:
            trace.visible = False
        with self.assertRaises(PlottingError):
            self.module.draw(self.axes, traces, options_for(self.module))

    def test_length_mismatch_names_the_trace(self):
        traces = make_traces()
        traces[1] = SimpleTrace("short", np.zeros(3))
        with self.assertRaises(PlottingError) as caught:
            self.module.draw(self.axes, traces, options_for(self.module))
        self.assertIn("short", str(caught.exception))

    def test_outside_legend_goes_on_the_figure(self):
        options = options_for(self.module, **{"Legend": True,
                                              "Legend Location": "outside right upper"})
        self.module.draw(self.axes, make_traces(), options)
        self.assertTrue(self.axes.get_figure().legends)
        self.assertIsNone(self.axes.get_legend())

    def test_refresh_does_not_stack_legends(self):
        options = options_for(self.module, **{"Legend": True})
        self.module.draw(self.axes, make_traces(), options)
        for _ in range(3):
            self.module.refresh(self.axes, options)
        self.assertEqual(len(self.axes.get_figure().legends), 0)
        self.assertIsNotNone(self.axes.get_legend())


class StylingTests(unittest.TestCase):
    def setUp(self):
        self.module = plotting.load_mode("XY Plot")
        self.axes = make_axes()

    def draw_with(self, **values):
        options = options_for(self.module, **values)
        self.module.draw(self.axes, make_traces(), options)
        return options

    def test_manual_limits_and_ticks(self):
        self.draw_with(**{"Manual limits (X)": True, "Min X": 1.0, "Max X": 5.0,
                          "X tick interval": 1.0})
        self.assertEqual(self.axes.get_xlim(), (1.0, 5.0))
        self.assertIn(5.0, list(self.axes.get_xticks()))

    def test_zero_tick_interval_keeps_automatic_ticks(self):
        self.draw_with(**{"Manual limits (X)": True, "Min X": 1.0, "Max X": 5.0,
                          "X tick interval": 0.0})
        self.assertEqual(self.axes.get_xlim(), (1.0, 5.0))

    def test_absurd_tick_interval_is_refused_not_hung(self):
        with self.assertRaises(OptionError) as caught:
            self.draw_with(**{"Manual limits (X)": True, "Min X": 0.0, "Max X": 1.0,
                              "X tick interval": 1e-6})
        self.assertIn(str(MAX_TICKS), str(caught.exception))

    def test_inverted_limits_are_refused(self):
        with self.assertRaises(OptionError):
            self.draw_with(**{"Manual limits (Y)": True, "Min Y": 5.0, "Max Y": 1.0})

    def test_log_axis_rejects_non_positive_minimum(self):
        with self.assertRaises(OptionError):
            self.draw_with(**{"Log X Axis": True, "Manual limits (X)": True,
                              "Min X": 0.0, "Max X": 10.0})

    def test_log_axis_is_applied_on_both_axes(self):
        self.draw_with(**{"Log X Axis": True, "Log Y Axis": True})
        self.assertEqual(self.axes.get_xscale(), "log")
        self.assertEqual(self.axes.get_yscale(), "log")

    def test_line_width_applies_to_existing_lines(self):
        options = self.draw_with(**{"Line Width": 1.0})
        wider = Options.from_specs(self.module.get_option_specs(), {"Line Width": 4.0})
        apply_axes_style(self.axes, wider)
        self.assertEqual(self.axes.lines[0].get_linewidth(), 4.0)
        self.assertIsNotNone(options)


class ParametricTests(unittest.TestCase):
    def setUp(self):
        self.module = plotting.load_mode("Parametric")

    def test_numeric_headers_become_engineering_labels(self):
        options = options_for(self.module, **{"Parameter's Name": "W",
                                              "Parameter's Unit": "m"})
        label = self.module.format_label("1e-06", options)
        self.assertTrue(label.startswith("W="))
        self.assertIn("m", label)

    def test_non_numeric_headers_survive_unchanged(self):
        options = options_for(self.module, **{"Parameter's Name": "corner"})
        self.assertEqual(self.module.format_label("tt", options), "corner=tt")


class PairedColumnsTests(unittest.TestCase):
    def setUp(self):
        self.module = plotting.load_mode("Paired Columns")
        self.axes = make_axes()

    def test_pairs_are_consumed_two_at_a_time(self):
        traces = make_traces() + [SimpleTrace("3e-06", np.ones(25))]
        self.module.draw(self.axes, traces, options_for(self.module))
        self.assertEqual(len(self.axes.lines), 2)

    def test_a_single_column_is_refused(self):
        with self.assertRaises(PlottingError):
            self.module.draw(self.axes, [SimpleTrace("only", np.zeros(4))],
                             options_for(self.module))


class HistogramTests(unittest.TestCase):
    def setUp(self):
        self.module = plotting.load_mode("Histogram")
        self.axes = make_axes()
        rng = np.random.default_rng(0)
        self.traces = [
            SimpleTrace("run A", rng.normal(0.9, 0.02, 200)),
            SimpleTrace("run B", rng.normal(0.8, 0.02, 200)),
        ]

    def test_grouped_bars_do_not_overlap(self):
        options = options_for(self.module, **{"Number of Bins": 4})
        self.module.draw(self.axes, self.traces, options)
        # 2 traces x 4 bins, and every bar narrower than one bin slot.
        self.assertEqual(len(self.axes.patches), 8)
        self.assertTrue(all(patch.get_width() <= 0.5 for patch in self.axes.patches))

    def test_monte_carlo_mode_draws_each_visible_trace(self):
        options = options_for(self.module, **{"Monte Carlo Mode": True,
                                              "Number of Bins": 6})
        self.module.draw(self.axes, self.traces, options)
        self.assertTrue(self.axes.patches)

    def test_all_nan_input_is_reported(self):
        options = options_for(self.module)
        traces = [SimpleTrace("empty", np.full(10, np.nan))]
        with self.assertRaises(PlottingError):
            self.module.draw(self.axes, traces, options)

    def test_constant_data_does_not_divide_by_zero(self):
        options = options_for(self.module, **{"Number of Bins": 3})
        traces = [SimpleTrace("flat", np.full(20, 0.5))]
        self.module.draw(self.axes, traces, options)
        self.assertTrue(self.axes.patches)

    def test_bin_range_labels_survive_refresh(self):
        options = options_for(self.module, **{"Number of Bins": 3, "Decimals": 1})
        self.module.draw(self.axes, self.traces, options)
        self.module.refresh(self.axes, options)
        labels = [label.get_text() for label in self.axes.get_xticklabels()]
        self.assertEqual(len(labels), 3)
        self.assertTrue(all(chr(10) in label for label in labels), labels)

    def test_percent_formatter_survives_refresh(self):
        options = options_for(self.module, **{"Monte Carlo Mode": True,
                                              "Percent X Axis": True,
                                              "Decimals": 0})
        self.module.draw(self.axes, self.traces[:1], options)
        self.module.refresh(self.axes, options)
        formatted = self.axes.xaxis.get_major_formatter()(90.0)
        self.assertIn("%", formatted)

    def test_more_traces_than_the_palette_still_get_colors(self):
        rng = np.random.default_rng(1)
        traces = [SimpleTrace(f"t{i}", rng.normal(0.5, 0.1, 50)) for i in range(12)]
        self.module.draw(self.axes, traces, options_for(self.module))
        self.assertEqual(len({patch.get_facecolor() for patch in self.axes.patches}), 12)


if __name__ == "__main__":
    unittest.main()
