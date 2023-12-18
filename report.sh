# generate allure html report
allure generate ./report/raw -o ./report/html --clean

# open allure html report
allure open ./report/html