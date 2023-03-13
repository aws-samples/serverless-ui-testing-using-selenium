import os
import json
import boto3
import random
import time
import string
import urllib
import inspect
import traceback
import subprocess
from datetime import datetime
from selenium import webdriver
from pyvirtualdisplay import Display
from botocore.exceptions import ClientError
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Log
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

br = os.environ['BROWSER'].lower()
br_version = os.environ['BROWSER_VERSION']
driver_version = os.environ['DRIVER_VERSION']

s3 = boto3.client('s3')
ddb = boto3.client('dynamodb')
sfn = boto3.client('stepfunctions')
enable_display = False

if 'DISPLAY' in os.environ and os.environ['DISPLAY'] == ':25':
    enable_display = True

if enable_display:
    display = Display(visible=False, extra_args=[':25'], size=(2560, 1440)) 
    display.start()
    print('Started Display %s' % os.environ['DISPLAY'])

if br == 'firefox':
    firefox_options = FirefoxOptions()
    if not enable_display:
        firefox_options.add_argument("-headless")
    firefox_options.add_argument("-safe-mode")
    firefox_options.add_argument('-width 2560')
    firefox_options.add_argument('-height 1440')
    random_dir = '/tmp/' + ''.join(random.choice(string.ascii_lowercase) for i in range(8))
    os.mkdir(random_dir)
    ff_profile = webdriver.FirefoxProfile(profile_directory=random_dir)
    driver = webdriver.Firefox(firefox_profile=ff_profile,
                               firefox_binary='/opt/firefox/' + br_version + '/firefox',
                               executable_path='/opt/geckodriver/' + driver_version + '/geckodriver',
                               options=firefox_options,
                               service_log_path='/tmp/geckodriver.log')
    print('Started Firefox Driver')
elif br == 'chrome':
    chrome_options = ChromeOptions()
    if not enable_display:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-tools")
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("window-size=2560x1440")
    chrome_options.add_argument("--user-data-dir=/tmp/chrome-user-data")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.binary_location = '/opt/chrome/' + br_version + '/chrome'
    driver = webdriver.Chrome(executable_path='/opt/chromedriver/' + driver_version + '/chromedriver',
                              options=chrome_options,
                              service_log_path='/tmp/chromedriver.log')
    if driver:
        print('Started Chrome Driver')
else:
    print('Unsupported browser %s' % br)


def funcname():
    return inspect.stack()[1][3]


def update_status(mod, tc, st, et, ss, er, trun, status_table):
    if et != ' ':
        t_t = str(int(round((datetime.strptime(et, '%d-%m-%Y %H:%M:%S,%f') -
                             datetime.strptime(st, '%d-%m-%Y %H:%M:%S,%f')).microseconds, -3) / 1000))
    else:
        t_t = ' '
    try:
        if er:
            ddb.update_item(Key={'testrunid': {'S': trun}, 'testcaseid': 
                                              {'S': mod + '-' + br + '_' + br_version + '-' + tc}},
                            UpdateExpression="set details.StartTime = :st, details.EndTime = :e, details.#S = :s," +
                            "details.ErrorMessage = :er, details.TimeTaken = :tt",
                            ExpressionAttributeValues={':e': {'S': et}, ':s': {'S': ss}, ':st': {'S': st},
                                                       ':er': {'S': er}, ':tt': {'S': t_t}},
                            TableName=status_table, ExpressionAttributeNames={'#S': 'Status'})
        else:
            ddb.update_item(Key={'testrunid': {'S': trun}, 'testcaseid':
                                              {'S': mod + '-' + br + '_' + br_version + '-' + tc}},
                            UpdateExpression="set details.StartTime = :st, details.EndTime = :e, details.#S = :s," +
                                             "details.TimeTaken = :tt",
                            ExpressionAttributeValues={':e': {'S': et}, ':s': {'S': ss}, ':st': {'S': st},
                                                       ':tt': {'S': t_t}},
                            TableName=status_table, ExpressionAttributeNames={'#S': 'Status'})
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationException':
            ddb.update_item(Key={'testrunid': {'S': trun}, 'testcaseid':
                                              {'S': mod + '-' + br + '_' + br_version + '-' + tc}},
                            UpdateExpression="set #atName = :atValue", ExpressionAttributeValues={
                            ':atValue': {'M': {'StartTime': {'S': st}, 'EndTime': {'S': et}, 'Status': {'S': ss},
                                               'ErrorMessage': {'S': er}, 'TimeTaken': {'S': t_t}}}},
                            TableName=status_table,
                            ExpressionAttributeNames={'#atName': 'details'})
        else:
            traceback.print_exc()
    except:
        traceback.print_exc()


def tc0001(browser, mod, tc, s3buck, s3prefix, trun, main_url, status_table):
    # Testcase to validate whether home page is displayed properly
    fname = mod + '-' + tc + '.png'
    fpath = '/tmp/' + fname
    starttime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
    endtime = ' '
    try:
        update_status(mod, tc, starttime, endtime, 'Started', ' ', trun, status_table)
        browser.get(main_url)
        assert 'Serverless UI Testing' in browser.title
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'kp')))
        browser.get_screenshot_as_file(fpath)
        with open(fpath, 'rb') as data:
            s3.upload_fileobj(data, s3buck, s3prefix + fname)
        os.remove(fpath)
        print('Completed test %s' % funcname())
        endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
        update_status(mod, tc, starttime, endtime, 'Passed', ' ', trun, status_table)
        return {"status": "Success", "message": "Successfully executed TC0001"}
    except:
        print('Failed while running test %s' % funcname())
        endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
        update_status(mod, tc, starttime, endtime, 'Failed', traceback.print_exc(), trun, status_table)
        return {"status": "Failed", "message": "Failed to execute TC0001. Check logs for details."}


def tc0002(browser, mod, tc, s3buck, s3prefix, trun, main_url, status_table):
    # Testcase to validate whether button click is displayed properly
    fname = mod + '-' + tc + '.png'
    fpath = '/tmp/' + fname
    starttime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
    endtime = ' '
    todisplay = 'Serverless is a way to describe the services, practices, and strategies ' + \
                'that enable you to build more agile applications so you can innovate and ' + \
                'respond to change faster.'
    try:
        update_status(mod, tc, starttime, endtime, 'Started', ' ', trun, status_table)
        browser.get(main_url)
        assert 'Serverless UI Testing' in browser.title
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'kp')))
        browser.find_element_by_xpath("//*[@id='bc']/a").click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'displaybtn')))
        assert 'Serverless UI Testing - Button Click.' in browser.title
        browser.find_element_by_id('displaybtn').click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'cbbutton')))
        displayed = browser.find_element_by_id('cbbutton').text
        browser.get_screenshot_as_file(fpath)
        with open(fpath, 'rb') as data:
            s3.upload_fileobj(data, s3buck, s3prefix + fname)
        os.remove(fpath)
        print('Completed test %s' % funcname())
        if todisplay == displayed:
            endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
            update_status(mod, tc, starttime, endtime, 'Passed', ' ', trun, status_table)
            return {"status": "Success", "message": "Successfully executed TC0002"}
        else:
            endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
            update_status(mod, tc, starttime, endtime, 'Failed', 'Didn\'t find the expected text to be displayed.', trun, status_table)
            return {"status": "Failed", "message": "Failed to execute TC0002. Check logs for details."}
    except:
        print('Failed while running test %s' % funcname())
        traceback.print_exc()
        endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
        update_status(mod, tc, starttime, endtime, 'Failed', traceback.print_exc(), trun, status_table)
        return {"status": "Failed", "message": "Failed to execute TC0002. Check logs for details."}

def tc0011(browser, mod, tc, s3buck, s3prefix, trun, main_url, status_table):
    try:
        if enable_display:
            filepath = '/tmp/'
            recorder = subprocess.Popen(['/usr/bin/ffmpeg', '-f', 'x11grab', '-video_size',
                                         '2560x1440', '-framerate', '25', '-probesize',
                                         '10M', '-i', ':25', '-y', filepath + 'tc0011.mp4'])
            time.sleep(0.5)
        print('Getting URL')
        starttime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
        endtime = ' '
        update_status(mod, tc, starttime, endtime, 'Started', ' ', trun, status_table)
        browser.get(main_url)
        assert 'Serverless UI Testing' in browser.title
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'kp')))
        browser.find_element_by_xpath("//*[@id='bc']/a").click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'displaybtn')))
        assert 'Serverless UI Testing - Button Click.' in browser.title
        browser.find_element_by_id('displaybtn').click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'cbbutton')))
        browser.get(main_url)
        assert 'Serverless UI Testing' in browser.title
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'kp')))
        browser.find_element_by_xpath("//*[@id='cb']/a").click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'box3')))
        assert 'Serverless UI Testing - Check Box.' in browser.title
        browser.find_element_by_id('box1').click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'cbbox1')))
        browser.get(main_url)
        assert 'Serverless UI Testing' in browser.title
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'kp')))
        browser.find_element_by_xpath("//*[@id='dd']/a").click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.NAME, 'cbdropdown')))
        assert 'Serverless UI Testing - Dropdown' in browser.title
        browser.find_element_by_id('CP').click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'dvidrop')))
        browser.get(main_url)
        assert 'Serverless UI Testing' in browser.title
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'kp')))
        browser.find_element_by_xpath("//*[@id='img']/a").click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'image1')))
        assert 'Serverless UI Testing - Images' in browser.title
        browser.get(main_url)
        assert 'Serverless UI Testing' in browser.title
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'kp')))
        browser.find_element_by_xpath("//*[@id='kp']/a").click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'titletext')))
        assert 'Serverless UI Testing - Key Press.' in browser.title
        endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
        if enable_display:
            recorder.terminate()
            time.sleep(7)
            print('Closed recorder')
            recorder.wait(timeout=20)
        update_status(mod, tc, starttime, endtime, 'Passed', ' ', trun, status_table)
        try:
            if enable_display:
                s3.upload_file('/tmp/tc0011.mp4', s3buck, s3prefix + 'tc0011.mp4')
                os.remove('/tmp/tc0011.mp4')
            return {"status": "Success", "message": "Successfully executed TC0011"}
        except:
            traceback.print_exc()
            return {"status": "Failed", "message": "Failed to upload video to S3"}
    except:
        traceback.print_exc()
        s3.upload_file('/tmp/chromedriver.log', s3buck, s3prefix + 'chromedriver.log')
        if recorder:
            recorder.terminate()
        return {"status": "Failed", "message": "Failed to execute TC0011. Check logs for details."}


def tc0003(browser, mod, tc, s3buck, s3prefix, trun, main_url, status_table):
    # Testcase to validate whether reset button is working properly
    fname = mod + '-' + tc + '.png'
    fpath = '/tmp/' + fname
    starttime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
    endtime = ' '
    try:
        update_status(mod, tc, starttime, endtime, 'Started', ' ', trun, status_table)
        browser.get(main_url)
        assert 'Serverless UI Testing' in browser.title
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'kp')))
        browser.find_element_by_xpath("//*[@id='bc']/a").click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'displaybtn')))
        assert 'Serverless UI Testing - Button Click.' in browser.title
        browser.find_element_by_id('displaybtn').click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'cbbutton')))
        displayed = browser.find_element_by_id('cbbutton').text
        browser.find_element_by_id('resetbtn').click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'cbbutton')))
        displayed = browser.find_element_by_id('cbbutton').text
        browser.get_screenshot_as_file(fpath)
        with open(fpath, 'rb') as data:
            s3.upload_fileobj(data, s3buck, s3prefix + fname)
        os.remove(fpath)
        print('Completed test %s' % funcname())
        if displayed:
            endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
            update_status(mod, tc, starttime, endtime, 'Failed',
                          'Text was not reset as expected.', trun, status_table)
            return {"status": "Failed", "message":
                    "Failed to execute TC0003. Text was not reset as expected."}
        else:
            endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
            update_status(mod, tc, starttime, endtime, 'Passed', ' ', trun, status_table)
            return {"status": "Success", "message": "Successfully executed TC0003"}
    except:
        print('Failed while running test %s' % funcname())
        endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
        update_status(mod, tc, starttime, endtime, 'Failed', traceback.print_exc(), trun, status_table)
        return {"status": "Failed", "message":
                "Failed to execute TC0003. Check logs for details."}


def tc0004(browser, mod, tc, s3buck, s3prefix, trun, main_url, status_table):
    # Testcase to validate whether check box is working properly
    fname = mod + '-' + tc + '.png'
    fpath = '/tmp/' + fname
    starttime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
    endtime = ' '
    try:
        update_status(mod, tc, starttime, endtime, 'Started', ' ', trun, status_table)
        browser.get(main_url)
        assert 'Serverless UI Testing' in browser.title
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'kp')))
        browser.find_element_by_xpath("//*[@id='cb']/a").click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'box3')))
        assert 'Serverless UI Testing - Check Box.' in browser.title
        browser.find_element_by_id('box1').click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'cbbox1')))
        displayed = browser.find_element_by_id('cbbox1').text
        if displayed != 'Checkbox 1 checked.':
            endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
            update_status(mod, tc, starttime, endtime, 'Failed',
                          'Checkbox1 text was not displayed.', trun, status_table)
            return {"status": "Failed", "message": "Checkbox1 text was not displayed."}
        browser.find_element_by_id('box2').click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'cbbox2')))
        displayed = browser.find_element_by_id('cbbox2').text
        if displayed != 'Checkbox 2 checked.':
            endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
            update_status(mod, tc, starttime, endtime, 'Failed',
                          'Checkbox2 text was not displayed.', trun, status_table)
            return {"status": "Failed", "message": "Checkbox2 text was not displayed."}
        browser.find_element_by_id('box1').click()
        WebDriverWait(browser, 20).until_not(EC.visibility_of_element_located((By.ID, 'cbbox1')))
        displayed = browser.find_element_by_id('cbbox1').text
        if displayed:
            endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
            update_status(mod, tc, starttime, endtime, 'Failed',
                          'Checkbox1 text was displayed after unchecking.', trun, status_table)
            return {"status": "Failed", "message":
                    "Checkbox1 text was displayed after unchecking."}
        browser.get_screenshot_as_file(fpath)
        with open(fpath, 'rb') as data:
            s3.upload_fileobj(data, s3buck, s3prefix + fname)
        os.remove(fpath)
        print('Completed test %s' % funcname())
        endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
        update_status(mod, tc, starttime, endtime, 'Passed', ' ', trun, status_table)
        return {"status": "Success", "message": "Successfully executed TC0004"}
    except:
        print('Failed while running test %s' % funcname())
        endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
        update_status(mod, tc, starttime, endtime, 'Failed', traceback.print_exc(), trun, status_table)
        return {"status": "Failed", "message":
                "Failed to execute TC0004. Check logs for details."}


def tc0005(browser, mod, tc, s3buck, s3prefix, trun, main_url, status_table):
    # Testcase to validate whether dropdown is working properly
    fname = mod + '-' + tc + '.png'
    fpath = '/tmp/' + fname
    starttime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
    endtime = ' '
    try:
        update_status(mod, tc, starttime, endtime, 'Started', ' ', trun, status_table)
        browser.get(main_url)
        assert 'Serverless UI Testing' in browser.title
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'kp')))
        browser.find_element_by_xpath("//*[@id='dd']/a").click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.NAME, 'cbdropdown')))
        assert 'Serverless UI Testing - Dropdown' in browser.title
        browser.find_element_by_id('CP').click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'dvidrop')))
        displayed = browser.find_element_by_id('dvidrop').text
        cp_text = 'AWS CodePipeline is a continuous integration and continuous delivery service ' + \
                  'for fast and reliable application and infrastructure updates.'
        if displayed != cp_text:
            endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
            update_status(mod, tc, starttime, endtime, 'Failed',
                          'Expected text for CodePipeline from dropdown was not displayed.', trun, status_table)
            return {"status": "Failed", "message":
                    "Expected text for CodePipeline from dropdown was not displayed."}
        browser.find_element_by_id('CC').click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'dvidrop')))
        displayed = browser.find_element_by_id('dvidrop').text
        cc_text = 'AWS CodeCommit is a fully-managed source control service that makes it easy for ' + \
                  'companies to host secure and highly scalable private Git repositories.'
        if displayed != cc_text:
            endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
            update_status(mod, tc, starttime, endtime, 'Failed',
                          'Expected text for CodeCommit from dropdown was not displayed.', trun, status_table)
            return {"status": "Failed", "message":
                    "Expected text for CodeCommit from dropdown was not displayed."}
        browser.find_element_by_id('CB').click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'dvidrop')))
        displayed = browser.find_element_by_id('dvidrop').text
        cb_text = 'AWS CodeBuild is a fully managed build service that compiles source code, ' + \
                  'runs tests, and produces software packages that are ready to deploy.'
        if displayed != cb_text:
            endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
            update_status(mod, tc, starttime, endtime, 'Failed',
                          'Expected text for CodeBuild from dropdown was not displayed.', trun, status_table)
            return {"status": "Failed", "message":
                    "Expected text for CodeBuild from dropdown was not displayed."}
        browser.find_element_by_id('CD').click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'dvidrop')))
        displayed = browser.find_element_by_id('dvidrop').text
        cd_text = 'AWS CodeDeploy is a service that automates code deployments to any instance, ' + \
                  'including Amazon EC2 instances and instances running on-premises.'
        if displayed != cd_text:
            endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
            update_status(mod, tc, starttime, endtime, 'Failed',
                          'Expected text for CodeDeploy from dropdown was not displayed.', trun, status_table)
            return {"status": "Failed", "message":
                    "Expected text for CodeDeploy from dropdown was not displayed."}
        browser.find_element_by_id('CS').click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'dvidrop')))
        displayed = browser.find_element_by_id('dvidrop').text
        cs_text = 'AWS CodeStar enables you to quickly develop, build, and deploy applications on AWS. ' + \
                  'AWS CodeStar provides a unified user interface, enabling you to easily manage your ' + \
                  'software development activities in one place.'
        if displayed != cs_text:
            endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
            update_status(mod, tc, starttime, endtime, 'Failed',
                          'Expected text for CodeStar from dropdown was not displayed.', trun, status_table)
            return {"status": "Failed", "message":
                    "Expected text for CodeStar from dropdown was not displayed."}
        browser.find_element_by_id('emp').click()
        # WebDriverWait(browser, 120).until(EC.visibility_of_element_located((By.ID, 'dvidrop')))
        displayed = browser.find_element_by_id('dvidrop').text
        if displayed:
            endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
            update_status(mod, tc, starttime, endtime, 'Failed', 'Expected no text', trun, status_table)
            return {"status": "Failed", "message": "Expected no text."}
        browser.get_screenshot_as_file(fpath)
        with open(fpath, 'rb') as data:
            s3.upload_fileobj(data, s3buck, s3prefix + fname)
        os.remove(fpath)
        print('Completed test %s' % funcname())
        endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
        update_status(mod, tc, starttime, endtime, 'Passed', ' ', trun, status_table)
        return {"status": "Success", "message": "Successfully executed TC0005"}
    except:
        print('Failed while running test %s' % funcname())
        endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
        update_status(mod, tc, starttime, endtime, 'Failed', traceback.print_exc(), trun, status_table)
        return {"status": "Failed", "message":
                "Failed to execute TC0005. Check logs for details."}


def tc0006(browser, mod, tc, s3buck, s3prefix, trun, main_url, status_table):
    # Testcase to validate whether images page is working properly
    fname = mod + '-' + tc + '.png'
    fpath = '/tmp/' + fname
    starttime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
    endtime = ' '
    try:
        update_status(mod, tc, starttime, endtime, 'Started', ' ', trun, status_table)
        browser.get(main_url)
        assert 'Serverless UI Testing' in browser.title
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'kp')))
        browser.find_element_by_xpath("//*[@id='img']/a").click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'image1')))
        assert 'Serverless UI Testing - Images' in browser.title
        image_list = browser.find_elements_by_tag_name('img')
        for image in image_list:
            imageurl = image.get_attribute('src')
            imgfile = imageurl.split('/')[-1]
            try:
                urllib.request.urlopen(urllib.request.Request(imageurl, method='HEAD'))
            except urllib.error.HTTPError as err:
                if err.code == 403 and imgfile != 'test3.png':
                    endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
                    update_status(mod, tc, starttime, endtime, 'Failed', 'Expected images not displayed.', trun, status_table)
                    return {"status": "Failed", "message":
                            "Expected images not displayed.. Check logs for details."}
        print('Completed test %s' % funcname())
        browser.get_screenshot_as_file(fpath)
        with open(fpath, 'rb') as data:
            s3.upload_fileobj(data, s3buck, s3prefix + fname)
        os.remove(fpath)
        endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
        update_status(mod, tc, starttime, endtime, 'Passed', ' ', trun, status_table)
        return {"status": "Success", "message": "Successfully executed TC0006"}
    except:
        print('Failed while running test %s' % funcname())
        endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
        update_status(mod, tc, starttime, endtime, 'Failed', traceback.print_exc(), trun, status_table)
        return {"status": "Failed", "message":
                "Failed to execute TC0006. Check logs for details."}


def tc0007(browser, mod, tc, s3buck, s3prefix, trun, main_url, status_table):
    # Testcase to validate whether keypress page is working properly
    fname = mod + '-' + tc + '.png'
    fpath = '/tmp/' + fname
    key_pos = [Keys.ALT, Keys.CONTROL, Keys.DOWN, Keys.ESCAPE, Keys.F1, Keys.F10, Keys.F11, Keys.F12, Keys.F2,
               Keys.F3, Keys.F4, Keys.F5, Keys.F6, Keys.F7, Keys.F8, Keys.F9, Keys.LEFT, Keys.SHIFT, Keys.SPACE,
               Keys.TAB, Keys.UP]
    key_word = ['ALT', 'CONTROL', 'DOWN', 'ESCAPE', 'F1', 'F10', 'F11', 'F12', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7',
                'F8', 'F9', 'LEFT', 'SHIFT', 'SPACE', 'TAB', 'UP']
    starttime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
    endtime = ' '
    try:
        update_status(mod, tc, starttime, endtime, 'Started', ' ', trun, status_table)
        browser.get(main_url)
        assert 'Serverless UI Testing' in browser.title
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'kp')))
        browser.find_element_by_xpath("//*[@id='kp']/a").click()
        WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.ID, 'titletext')))
        assert 'Serverless UI Testing - Key Press.' in browser.title
        actions = webdriver.ActionChains(browser)
        actions.move_to_element(browser.find_element_by_id('titletext'))
        actions.click()
        rnum = random.randrange(0, 20)
        actions.send_keys(key_pos[rnum])
        actions.perform()
        WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.ID, 'keytext')))
        displayed = browser.find_element_by_id('keytext').text
        if displayed != 'You pressed \'' + key_word[rnum] + '\' key.':
            endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
            update_status(mod, tc, starttime, endtime, 'Failed', 'Expected key press not displayed.', trun, status_table)
            return {"status": "Failed", "message": "Expected key press not displayed"}
        print('Completed test %s' % funcname())
        browser.get_screenshot_as_file(fpath)
        with open(fpath, 'rb') as data:
            s3.upload_fileobj(data, s3buck, s3prefix + fname)
        os.remove(fpath)
        endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
        update_status(mod, tc, starttime, endtime, 'Passed', ' ', trun, status_table)
        return {"status": "Success", "message": "Successfully executed TC0007"}
    except:
        print('Failed while running test %s' % funcname())
        endtime = datetime.strftime(datetime.today(), '%d-%m-%Y %H:%M:%S,%f')
        update_status(mod, tc, starttime, endtime, 'Failed', traceback.print_exc(), trun, status_table)
        return {"status": "Failed", "message":
                "Failed to execute TC0007. Check logs for details."}


def lambda_handler(event, context):
    'Lambda Handler'
    # print('Inside Handler')
    print(event)
    tc_name = event['tcname']
    browser = driver
    if not browser:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({ "message": "Unsupported browser: %s" % br })
        }
    # print('Before calling method :' + tc_name)
    s3prefix = event['s3prefix'] + event['testrun'].split(':')[-1] + '/' + br + '/'
    resp = globals().get(tc_name)(browser, event['module'], tc_name, event['s3buck'], s3prefix,
                         event['testrun'].split(':')[-1], event['WebURL'], event['StatusTable'])
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "message": resp['message']
        })
    }

def container_handler():
    'Container Handler'
    tc_name = os.environ['tcname']
    browser = driver
    if not browser:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({ "message": "Unsupported browser: %s" % br })
        }
    # print('Before calling method :' + tc_name)
    s3prefix = os.environ['s3prefix'] + os.environ['testrun'].split(':')[-1] + '/' + br + '/'
    resp = globals().get(tc_name)(browser, os.environ['module'], tc_name, os.environ['s3buck'], s3prefix,
                                  os.environ['testrun'].split(':')[-1], os.environ['WebURL'], os.environ['StatusTable'])
    sfn.send_task_success(
        taskToken=os.environ['TASK_TOKEN_ENV_VARIABLE'],
        output=json.dumps({"message": resp['message']})
    )
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "message": resp['message']
        })
    }
   
