# generate allure html report (allure needs to be installed first)
allure generate ./report/raw -o ./report/html --clean

# open allure html report (browser needs to be installed first)
allure open ./report/html
