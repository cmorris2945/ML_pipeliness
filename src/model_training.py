import os
import pandas as pd
import joblib   ### model saving
from sklearn.model_selection import RandomizedSearchCV
import lightgbm as lgb
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from src.logger import get_logger
from src.custom_exception import CustomException
from config.paths_config import *
from config.model_params import *
from utils.common_functions import read_yaml, load_data
from scipy.stats import randint
from config.paths_config import MODEL_OUTPUT_PATH


import mlflow
import mlflow.sklearn


logger = get_logger(__name__)

class ModelTraining:

    def __init__(self,  train_path, test_path, MODEL_OUTPUT_PATH):
        self.train_path = train_path
        self.test_path = test_path
        self.MODEL_OUTPUT_PATH = MODEL_OUTPUT_PATH

        self.params_dist = LIGHTGM_PARAMS
        self.random_search_params = RANDOM_SEARCH_PARAMS

    
    def load_and_split_data(self):

        try:
            logger.info(f"Loading data from {self.train_path}")
            train_df = load_data(self.train_path)

            logger.info(f"Now loading data from...{self.test_path}")
            test_df = load_data(self.test_path)

            X_train = train_df.drop(columns=["booking_status"])
            y_train = train_df["booking_status"]

            X_test = test_df.drop(columns=["booking_status"])
            y_test = test_df["booking_status"]

            logger.info("Data splitted and organized successfully for model training...")
            return X_train, y_train, X_test, y_test
        except Exception as e:
            logger.error(f"Error while loading data: {e}")
            raise CustomException("Failed to load you 'Jackass'", e)
        
    def train_lgbm(self, X_train, y_train):
        try:
            logger.info("Initializing your model...")

            lgbm_model = lgb.LGBMClassifier(random_state=self.random_search_params["random_state"])



            logger.info("Starting the hyterparamter tuning stuff...")

            random_search = RandomizedSearchCV(
                estimator=lgbm_model,
                param_distributions=self.params_dist,
                n_iter = self.random_search_params["n_iter"],
                cv = self.random_search_params["cv"],
                n_jobs = self.random_search_params["n_jobs"],
                verbose= self.random_search_params["verbose"],
                random_state=self.random_search_params["random_state"],
                scoring=self.random_search_params["scoring"]

            )
            logger.info("Starting your hyperparameter tuning...")
            random_search.fit(X_train, y_train)

            logger.info("The hyperparameter tuning is done.")

            best_params = random_search.best_params_
            best_lgbm_model = random_search.best_estimator_

            logger.info(f"Best parameters are: {best_params}")

            return best_lgbm_model
        
        except Exception as e:
            logger.error(f"Error while training model: {e}")
            raise CustomException("Failed to train model", e)
        
    def evaluate_model(self, model, X_test, y_test):
        try: 
            logger.info("Evaluating the model now...")

            y_pred = model.predict(X_test)

            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)

            logger.info(f"Accuracy Score: {accuracy}")
            logger.info(f"Precision Score: {precision}")
            logger.info(f"Recall Score: {recall}")
            logger.info(f"F1 Score: {f1}")

            return {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1": f1
            }
        except Exception as e:
            logger.error(f"Error while evaluating the model: {e}")
            raise CustomException("Failed to evaluate. Check your logs 'dipshit'", e)
        
    def save_model(self, model):
        try:
            os.makedirs(os.path.dirname(self.MODEL_OUTPUT_PATH), exist_ok=True)

            logger.info("saving the model....")
            joblib.dump(model, self.MODEL_OUTPUT_PATH)
            logger.info(f"Your model is saved at {self.MODEL_OUTPUT_PATH}")

        except Exception as e:
            logger.error(f"Error while saving the model: {e}")
            raise CustomException("Failed to save your 'stupid' model, shit for brains.", e)
        
    def run(self):
        try:
            with mlflow.start_run():
                logger.info("Starting the MODEL TRAINING PIPELINE...")

                logger.info("Starting the MLFLOW experimentation too.")
                logger.info("Logging the training and testing dataset to MLFLOW for later reference.")
                mlflow.log_artifact(self.train_path, artifact_path="datasets")
                mlflow.log_artifact(self.test_path, artifact_path="datasets")

                X_train,y_train, X_test, y_test = self.load_and_split_data()
                best_lgbm_model = self.train_lgbm(X_train,y_train)
                metrics = self.evaluate_model(best_lgbm_model, X_test, y_test)
                self.save_model(best_lgbm_model)

                logger.info("Logging the model into MLFLOW")
                mlflow.log_artifact(self.MODEL_OUTPUT_PATH)

                logger.info("Logging parameters and metrics to the MLFLOW")
                mlflow.log_params(best_lgbm_model.get_params())
                mlflow.log_metrics(metrics)

                logger.info("Model training finished....")

        except Exception as e:
            logger.error(f"Error in your model training pipeline: {e}")
            raise CustomException("Failed to run the pipeline!! Check the logs...!", e)
        
if __name__ == "__main__":
    trainer = ModelTraining(PROCESSED_TRAIN_DATA_PATH, PROCESSED_TEST_DATA_PATH, MODEL_OUTPUT_PATH)
    trainer.run()


        
                         








        







            



