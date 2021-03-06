# -*- coding: utf-8 -*-
import math
import unittest
import types
from collections import namedtuple
import numpy as np

from ..data import (
    Data,
    DataReader,
)

from ..feature import (
    Feature,
    FeatureBin,
    FeatureLin,
    FeatureNom,
    FeatureRank,
)


class FeatureTest(unittest.TestCase):
    def test__call__data(self):
        data = Data([[1, 2, 3],
                     [3, 4, 5]])
        self.assertEqual(data.features[0](data), [1, 3])
        self.assertEqual(data.features[1](data), [2, 4])
        self.assertEqual(data.features[2](data), [3, 5])

    def test__call__data_generator(self):
        data = Data((x for x in [[1, 2]]))
        self.assertTrue(
            isinstance(data.features[0](data), types.GeneratorType))
        self.assertEqual(list(data.features[0](data)), [1])

    def test__call__data__new_feature(self):
        f1, f2 = FeatureLin("f1"), FeatureLin("f2")
        data = Data([[2, 3],
                     [0, 1]], features=[f1, f2])
        self.assertEqual((f1 + f2)(data), [5, 1])
        self.assertEqual((f1 * f2)(data), [6, 0])


class DataTest(unittest.TestCase):
    def test_objects(self):
        data = Data([[1, 2]])
        Object = namedtuple('Object', ["f0", "f1"])
        objects_expected = [Object(1, 2)]
        self.assertEqual(data.objects, objects_expected)
        self.assertEqual(
            data.objects[0]._asdict(), objects_expected[0]._asdict())

    def test_objects_generator(self):
        data = Data((o for o in [[1, 2]]))
        self.assertTrue(isinstance(data.objects, types.GeneratorType))
        Object = namedtuple('Object', ["f0", "f1"])
        objects_expected = [Object(1, 2)]
        self.assertEqual(list(data.objects), objects_expected)

    def test_features_basic(self):
        data = Data([[0]])
        self.assertNotEqual(id(data.features), id(data._atomic_features))

    def test_objects_features(self):
        features = [FeatureLin("a")]
        f = features[0] + 1
        data = Data([[0]], features)
        data.features.append(f)
        self.assertEqual(data.objects[0], (0, 1))

    def test_objects_features_decrease(self):
        data = Data([[0, 1]])
        data.features = [data.features[0] - 1]
        objects_expected = [(-1, )]
        self.assertEqual(data.objects, objects_expected)

    def test_objects_features_constant(self):
        data = Data([[0]])
        data.features = [data.features[0] ** 0]
        objects_expected = [(1, )]
        self.assertEqual(data.objects, objects_expected)

    def test_init_features(self):
        self.data_file_content = "\n".join(
            [
                "# label:nom\tweight:lin\theigth:lin",
                "0\t70\t100.0",
                "1\t50\t200",
            ])
        self.data = DataReader.read(self.data_file_content.split("\n"))

        nfeatures = len(self.data_file_content.split("\n", 1)[0].split("\t"))
        self.assertEqual(
            len(self.data.features),
            nfeatures,
            "Error in parsing, check data.features length != %s" % nfeatures,
        )

        for feature in self.data.features:
            self.assertIsInstance(feature, Feature)

    def test__init__similar_features(self):
        with self.assertRaises(ValueError):
            Data([[0, 0]], [Feature("f0"), Feature("f0")])

    def test__eq__(self):
        objects1 = [(0, 1)]
        objects2 = [(1, 0)]
        features1 = [Feature("f1"), Feature("f2")]
        features2 = [Feature("f2"), Feature("f1")]
        self.assertEqual(Data(objects1), Data(objects1))
        self.assertEqual(Data(objects1, features1), Data(objects1, features1))
        self.assertEqual(Data(objects1, features1), Data(objects2, features2))

        self.assertNotEqual(
            Data(objects1, features1), Data(objects1, features2))

    def test_getitem_one(self):
        self.assertEqual(tuple(Data([[0]])[0, 0]), (0, ))

    def test_getitem(self):
        data = Data([(0, 1), (2, 3)])
        self.assertEqual(data[:], data)
        self.assertEqual(tuple(data[0, :]), (0, 1))
        self.assertEqual(tuple(data[0]), (0, 1))
        self.assertEqual(tuple(data[1]), (2, 3))
        self.assertEqual(data[:, 0], Data([(0, ), (2, )], [data.features[0]]))
        self.assertEqual(data[:, 1], Data([(1, ), (3, )], [data.features[1]]))

    def test_getitem_many(self):
        data = Data([(0, 1, 2)])
        self.assertEqual(data[:, 0:2], Data([(0, 1)], data.features[0:2]))
        self.assertEqual(data[:, :], data)

    def test_getitem_feature(self):
        data = Data([(0, 1)], [Feature("f1"), Feature("f2")])
        self.assertEqual(
            data[:, Feature("f1")], Data([(0, )], [Feature("f1")]))
        self.assertEqual(
            data[:, Feature("f2")], Data([(1, )], [Feature("f2")]))

    def test__add__different_number_objects(self):
        with self.assertRaises(ValueError):
            Data([[0], [1]], [Feature("f1")]) + Data([[1]], [Feature("f2")])

    def test__add__features_intersected(self):
        with self.assertRaises(ValueError):
            Data([(0, )]) + Data([(1, )])

    def test__add__(self):
        data1 = Data([[0]], [Feature("f1")]) + Data([[1]], [Feature("f2")])
        data2 = Data([[1]], [Feature("f2")]) + Data([[0]], [Feature("f1")])
        self.assertEqual(data1, data2, "Not commutative operation")
        self.assertEqual(data1, Data([[0, 1]], [Feature("f1"), Feature("f2")]))

    def test_vif_one_feature(self):
        with self.assertRaises(ValueError):
            Data([(0, )]).vif
            Data([(0, ), (1, )]).vif

    def test_vif_feateres_more_than_objects(self):
        with self.assertRaises(ValueError):
            Data([(0, 1)]).vif
            Data([(0, 1, 2), (1, 2, 3)]).vif

    def test_vif(self):
        data = Data([(0, 1), (1, 2)], [FeatureLin("f1"), FeatureLin("f2")])
        self.assertEqual(data.vif, [1.25, 0.25])

    def test_stat(self):
        features = [FeatureBin("f1"), FeatureNom("f2"),
                    FeatureRank("f3"), FeatureLin("f4")]
        data = Data([[True, "0", 0, 0.0],
                     [True, "0", 1, -1.0],
                     [False, "1", 2, 1.0]], features=features)
        expected = {
            FeatureBin("f1"): {True: 2, False: 1},
            FeatureNom("f2"): {"0": 2, "1": 1},
            FeatureRank("f3"): {0: 1, 1: 1, 2: 1},
            FeatureLin("f4"): {
                "mean": 0.0,
                "var": 2.0 / 3,
                "std": math.sqrt(2.0 / 3),
                "min": -1.0,
                "max": 1.0,
            }
        }

        self.assertEqual(data.stat, expected)

    def test_split_size(self):
        data = Data([[0], [1], [2]])
        d1, d2 = Data.split(data, size=1)
        self.assertTrue(isinstance(d1, Data))
        self.assertTrue(isinstance(d2, Data))
        self.assertEqual(d1.nobjects, 1)
        self.assertEqual(d2.nobjects, 2)

    def test_split_ratio(self):
        data = Data([[x] for x in range(100)])
        d1, d2 = Data.split(data, ratio=0.05)
        self.assertTrue(isinstance(d1, Data))
        self.assertTrue(isinstance(d2, Data))

        # probability of opposite = 8.44e-08
        self.assertTrue(d1.nobjects < 20)
        self.assertEqual(d1.nobjects + d2.nobjects, data.nobjects)

    def test_nfeatures(self):
        data = Data([[0]], [Feature("f1")]) + Data([[0]], [Feature("f2")])
        self.assertEqual(data.nfeatures, 2)

    def test_get_autoregression_data(self):
        data = Data([[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]])
        result = data.get_autoregression_data(data.features[0], period=3)
        result_expected = Data([[0, 2, 4], [2, 4, 6], [4, 6, 8]])
        self.assertEqual(result, result_expected)

    def test_matrix(self):
        data = Data([[0, 1], [2, 3], [4, 5]])
        matrix = np.matrix([[0, 1], [2, 3], [4, 5]])
        self.assertTrue((data.matrix == matrix).all())

        data.features.append(data.features[0] ** 2)
        matrix = np.matrix([[0, 1, 0], [2, 3, 4], [4, 5, 16]])
        self.assertTrue((data.matrix == matrix).all())


class DataReaderTest(unittest.TestCase):
    def setUp(self):
        self.header = "\t".join(["# label:nom", "weight:lin", "heigth:lin"])
        self.data_file_content = "\n".join(
            [
                self.header,
                "\t".join(["0", "70", "100.0"]),
                "\t".join(["1", "50", "200"]),
            ])

    def test_parse_header(self):
        features = DataReader._DataReader__parse_header(self.header)
        self.assertEqual(len(features), 3)

    def test_init_bad_header_hash(self):
        header = self.header[1:]
        with self.assertRaises(ValueError):
            DataReader._DataReader__parse_header(header)

    def test_init_duplicated_features(self):
        last_feature = self.header.rsplit("\t", 1)[-1]
        header = "\t".join([self.header, last_feature])
        with self.assertRaises(ValueError):
            DataReader._DataReader__parse_header(header)

    def test_init_skipped_feature_type(self):
        header = self.header.rsplit(":", 1)[0]
        features = DataReader._DataReader__parse_header(header)
        self.assertEqual(features[-1].scale, Feature.DEFAULT_SCALE)

    def test_get_duplicated_features(self):
        features = [Feature("f", scale="lin"), Feature("f")]
        duplicated_features =\
            DataReader._DataReader__get_duplicated_features(features)
        self.assertTrue(features[0] in duplicated_features)

    def test_get_objects_features(self):
        objects, features = DataReader.get_objects_features(
            self.data_file_content.split("\n"))
        self.assertEqual(len(features), 3)
        for feature in features:
            self.assertIsInstance(feature, Feature)

        objects_list = list(objects)
        self.assertEqual(len(objects_list), 2)
