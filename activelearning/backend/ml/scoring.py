

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

        :return: string
            A string containing the average scores in the results
        """
        av_accuracy = round(sum(self.accuracy)/len(self.accuracy), 3)
        av_precision = round(sum(self.precision) / len(self.precision), 3)
        av_recall = round(sum(self.recall) / len(self.recall), 3)
        av_f1 = round(sum(self.f1) / len(self.f1), 3)
        return f'              accuracy:  {av_accuracy}\n' + \
               f'              precision: {av_precision}\n' + \
               f'              recall:    {av_recall}\n' + \
               f'              f1 score:  {av_f1}\n'
