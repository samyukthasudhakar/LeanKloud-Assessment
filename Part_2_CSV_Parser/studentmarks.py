import csv

file = open('Student_marks_list.csv','r')

fileReader = csv.reader(file)

#storing the column headers onto a variable and iterating to the first row with value
header = next(fileReader)

#generating subject_toppers dicitonary with placeholder values
subject_toppers={}
for i in range(1,len(header)):
    subject_toppers[header[i]]=[0]

total_scores={}


#traverse through each student's marks
for row in fileReader:
    total=0

    # ->check if the score per subject is more than the current high score of the respective subject
    for i in range(1,len(header)):
        a=subject_toppers[header[i]]
        if a[0]<int(row[i]):
            a[0]=int(row[i])
            if len(a)>=2:
                del a[1:]
                a.append(row[0])
            else:
                a.append(row[0])
        elif a[0]==int(row[i]):
            a.append(row[0])

        # ->compute total marks
        total+=int(row[i])

    #store student's name and total score obtained 
    total_scores[row[0]]=total


# Format and print the toppers in each subject
for i in subject_toppers:

    output = "Topper in "+i+" is"
    name_list = subject_toppers[i][1:]

    if len(name_list)==1:
        print(output+" "+name_list[0])

    #formatting required when more than one student has scored the highest mark for a given subject 
    else:   
        for j in range(len(name_list)):
            if j==len(name_list)-2:
                output=output+" "+name_list[j]+" and "+name_list[j+1]
                print(output)
                break
            else:
                output=output+" "+name_list[j]+","
    

print()

#Format and print the top 3 students in the class based on their total score
best_students=[]

#sort the total_scores dictionary in descending order by value i.e., total score
for w in sorted(total_scores, key=total_scores.get, reverse=True):
    if len(best_students)<3:
        best_students.append(w)

print("Best students in class are "+best_students[0]+" , "+best_students[1]+" , "+best_students[2])
