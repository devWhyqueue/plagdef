from plagdef.gui.model import ResultsTableModel, ResultRow


def test_results_table_model_init(matches):
    model = ResultsTableModel(matches)
    assert model.rowCount() == 3
    assert model._rows[0] == ResultRow('doc1', 0, 5, 'doc2', 0, 5) \
           or model._rows[0] == ResultRow('doc2', 0, 5, 'doc1', 0, 5)


def test_results_table_model_data(matches):
    model = ResultsTableModel(matches)
    assert model.data(model.index(2, 0)) == 'doc3'
    assert model.data(model.index(2, 1)) == 2
    assert model.data(model.index(2, 2)) == 6
    assert model.data(model.index(2, 3)) == 'doc4'
    assert model.data(model.index(2, 4)) == 2
    assert model.data(model.index(2, 5)) == 8
