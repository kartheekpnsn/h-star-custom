from .eval_utils.evaluation_utils import agent_invoked_accuracy, compute_recall

class EvaluateAgentsCategories:
    def __init__(self):
        pass

    def __call__(self, ground_truth_categories, predicted_categories, **kwargs):
        expected = [expected_agent for expected_agent in ground_truth_categories]
        predicted = [predicted_agent for predicted_agent in predicted_categories]
        recall_k = {f"recall@{k}" : compute_recall(expected, predicted, k) for k in range(1, 4)}
        extra = {
            "agents_category_accuracy": agent_invoked_accuracy(predicted, expected),
            "agents_category_recall": compute_recall(expected, predicted, k=len(predicted)),
        }
        return dict(recall_k, **extra)
    

   