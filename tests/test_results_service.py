import unittest

from services.results_service import recent_results, save_analysis_result


class ResultsServiceTest(unittest.TestCase):
    def test_session_results_preserve_recent_first_flow(self):
        state = {}
        policy = {"days": 90, "max_records": 10}
        save_analysis_result({"metrics": {"keywords": 1}}, state=state, retention=policy)
        save_analysis_result({"metrics": {"keywords": 2}}, state=state, retention=policy)
        results = recent_results(state=state, max_records=10)
        self.assertEqual([item["result_data"]["metrics"]["keywords"] for item in results], [2, 1])

    def test_session_results_apply_max_records(self):
        state = {}
        policy = {"days": 90, "max_records": 2}
        for number in range(3):
            save_analysis_result({"metrics": {"keywords": number}}, state=state, retention=policy)
        self.assertEqual(len(recent_results(state=state, max_records=2)), 2)


if __name__ == "__main__":
    unittest.main()
