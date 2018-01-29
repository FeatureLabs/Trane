import json
from .prediction_problem import PredictionProblem
from ..ops import aggregation_ops, row_ops, transformation_ops, filter_ops
from ..utils.table_meta import TableMeta

import logging

__all__ = ['PredictionProblemGenerator']

class PredictionProblemGenerator:
    """Automatically generate prediction problems with a sequence of 
    fileter, row, transformation and aggregation operations.

    """
    def __init__(self, table_meta, entity_id_column, label_generating_column, time_column):
        """
        Args:
            label_generating_column: column to operate over. 
            entity_id_column: the column with entity id's. 
            time_column: the name of the column containing time information. 
        Returns:
            None
        """
        if isinstance(table_meta, list):
            table_meta = TableMeta(table_meta)
        assert isinstance(table_meta, TableMeta)
        self.table_meta = table_meta
        
        def check_column_type(column_name, data_type):
            assert(self.table_meta.get_type(column_name) == data_type)
            return column_name
        
        self.entity_id_column = check_column_type(entity_id_column, TableMeta.TYPE_IDENTIFIER)
        self.label_generating_column = check_column_type(label_generating_column, TableMeta.TYPE_FLOAT)
        self.time_column = check_column_type(time_column, TableMeta.TYPE_TIME)
        
        logging.info("Generate labels on [%s]" % self.label_generating_column)
        logging.info("Entites [%s]" % self.entity_id_column)
        logging.info("Time [%s]" % self.time_column)

    def generate(self):
        """Generate prediction problems.
        
        yeilds:
            PredictionProblem
        
        """
        #NOTE tricks for less indents
        def iter_over_ops():
            for aggregation_op_name in aggregation_ops.AGGREGATION_OPS:
                for transformation_op_name in transformation_ops.TRANSFORMATION_OPS:
                    for row_op_name in row_ops.ROW_OPS:
                        for filter_op_name in filter_ops.FILTER_OPS:
                            yield aggregation_op_name, transformation_op_name, \
                                row_op_name, filter_op_name

        for ops in iter_over_ops():
            for filter_column in self.table_meta.get_columns():
                aggregation_op_name, transformation_op_name, \
                    row_op_name, filter_op_name = ops
                    
                aggregation_op_obj = getattr(aggregation_ops, aggregation_op_name)(self.label_generating_column)    
                transformation_op_obj = getattr(transformation_ops, transformation_op_name)(self.label_generating_column)
                row_op_obj = getattr(row_ops, row_op_name)(self.label_generating_column)
                filter_op_obj = getattr(filter_ops, filter_op_name)(filter_column)

                prediction_problem = PredictionProblem(
                    [filter_op_obj, row_op_obj, transformation_op_obj, aggregation_op_obj])
                if not prediction_problem.op_type_check(self.table_meta):
                    continue
                yield prediction_problem