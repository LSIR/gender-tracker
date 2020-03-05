

""" Contains Classes to deal with results of training ML models """


class Results:
    """ Accumulates scores from different cross-validation passes """

    def __init__(self):
        """ Creates a new results object """
        self.accuracy = []
        self.precision = []
        self.recall = []
        self.f1 = []

    def add_scores(self, scores):
        """
        Adds new scores to the results.

        :param scores: dict
            The scores to add. Keys: accuracy, precision, recall, f1
        """
        self.accuracy.append(scores['accuracy'])
        self.precision.append(scores['precision'])
        self.recall.append(scores['recall'])
        self.f1.append(scores['f1'])

    def average_score(self):
        """
        Outputs the average scores as a string

        :return: float, float, float, float
            * The average accuracy
            * The average precision
            * The average recall
            * The average f1 score
        """
        acc = round(sum(self.accuracy)/len(self.accuracy), 3)
        pre = round(sum(self.precision) / len(self.precision), 3)
        rec = round(sum(self.recall) / len(self.recall), 3)
        f1 = round(sum(self.f1) / len(self.f1), 3)
        return acc, pre, rec, f1

    def print_average_score(self):
        """
        Outputs the average scores as a string

        :return: string
            A string containing the average scores in the results
        """
        acc, pre, rec, f1 = self.average_score()
        return f'              accuracy:  {acc}\n' + \
               f'              precision: {pre}\n' + \
               f'              recall:    {rec}\n' + \
               f'              f1 score:  {f1}\n'


class ResultAccumulator:
    """ Accumulates results from different models """

    def __init__(self):
        """ Creates a new results object """
        self.train_results = []
        self.test_results = []
        self.model_names = []

    def add_results(self, train_result, test_result, model_name):
        """
        Adds new model results to the accumulator

        :param train_result:
        :param test_result:
        :param model_name:
        :return:
        """
        self.train_results.append(train_result)
        self.test_results.append(test_result)
        self.model_names.append(model_name)

    def best_model(self):
        """
        Outputs the average scores as a string

        :return: string
            A string containing the average scores in the results
        """
        best_model = 0
        best_test_f1 = 0
        for i, test in enumerate(self.test_results):
            _, _, _, test_f1 = test.average_score()
            if test_f1 > best_test_f1:
                best_model = i
                best_test_f1 = test_f1
        return self.train_results[best_model], self.test_results[best_model], self.model_names[best_model]

