# Name: <Your Name>
# Date: <Date>
# Course Name: <Course Number/Name>
# Assignment Name: <Assignment Name>

import os
import datetime

def format_report(dir_name, tot, txt, py, csv, oth, old_n, new_n, bonus):
    """Formats and returns the text for the automation report."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = "AUTOMATION REPORT\n=================\n\n"
    report += "Directory: " + dir_name + "\n\n"
    report += "Total Files: " + str(tot) + "\n\n"
    report += "Text Files: " + str(txt) + "\n"
    report += "Python Files: " + str(py) + "\n"
    report += "CSV Files: " + str(csv) + "\n"
    report += "Other Files: " + str(oth) + "\n\n"
    report += "Oldest File: " + old_n + "\n"
    report += "Newest File: " + new_n + "\n\n"
    report += "Generated: " + now + "\n"
    
    if bonus != "":
        report += "\nBonus - Files older than 30 days:\n" + bonus
        
    return report

def write_report(content):
    """Writes the generated string to the text file."""
    report_file = open("automation_report.txt", "w")
    report_file.write(content)
    report_file.close()

def display_summary(tot, txt, py, csv, oth, old_n, new_n):
    """Prints the summary results to the console."""
    print("\nDirectory Analysis Complete\n")
    print("Total Files: " + str(tot) + "\n")
    print("Text Files: " + str(txt))
    print("Python Files: " + str(py))
    print("CSV Files: " + str(csv))
    print("Other Files: " + str(oth) + "\n")
    print("Oldest File: " + old_n)
    print("Newest File: " + new_n + "\n")
    print("Report written to automation_report.txt")

def process_dir(dir_name):
    """Analyzes directory contents and triggers output generation."""
    tot = txt = py = csv = oth = 0
    old_n = new_n = bonus = ""
    old_t = float('inf')
    new_t = -1.0

    for item in os.listdir(dir_name):
        path = os.path.join(dir_name, item)
        if os.path.isfile(path):
            tot += 1
            if item.endswith(".txt"): txt += 1
            elif item.endswith(".py"): py += 1
            elif item.endswith(".csv"): csv += 1
            else: oth += 1

            mtime = os.path.getmtime(path)
            if mtime < old_t:
                old_t = mtime
                old_n = item
            if mtime > new_t:
                new_t = mtime
                new_n = item

            f_date = datetime.datetime.fromtimestamp(mtime)
            if (datetime.datetime.now() - f_date).days > 30: bonus += item + "\n"

    content = format_report(dir_name, tot, txt, py, csv, oth, old_n, new_n, bonus)
    write_report(content)
    display_summary(tot, txt, py, csv, oth, old_n, new_n)

def main():
    """Main execution function with error handling."""
    print("Python Automation Report Generator\n")
    dir_name = input("Enter directory name: ")
    
    try:
        if not os.path.isdir(dir_name):
            print("\nDirectory does not exist. Ending program.")
            return
        
        process_dir(dir_name)
        
    except PermissionError:
        print("\nUnable to access directory.")
    except Exception:
        print("\nAn unexpected error occurred.")

if __name__ == "__main__":
    main()