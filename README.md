# LeanKloud Assessment
## Task - 1

A rest api built using ```flask-restplus``` framework for a simple todo application.


![API snippet](/images/API%20snippet.PNG)

## Task 2

A python script to traverse through a CSV file containing marks obtained by students of a class and print names of subject toppers and best students in the class.

**Time complexity : O( nm + nlogn )**

Here 
- ```n``` is the total number of records present in the CSV file
- ```m``` is the total number of subjects

```nm``` : The loop traverses through all the records of the csv file and for each record it runs for ```m``` times to extract the score obtained in each subject

```nlogn``` : To sort the dictionary containing student name and total score, inbuilt function ```sorted()``` is utilized. The ```sorted()``` function makes use of **Tim Sort**, a sorting algorithm based on Insertion Sort and Merge Sort thus resulting in a complexity of nlogn.

## Demo

Check out the demo of the applications [here](https://drive.google.com/file/d/1t9k9LmN9qkU5QAX7iQwtpvC9B_CH9A_r/view?usp=sharing).
