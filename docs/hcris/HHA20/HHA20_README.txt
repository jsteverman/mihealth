HCRIS PRODUCTION NOTES FOR HOME HEALTH AGENCY 2020 (HHA20) COST REPORT DATA

1. OVERVIEW
2. INTRODUCTION
3. NOTES
4. FILES AND CONTENT
5. SET UP GUIDANCE
6. DISCLAIMER OF WARRANTY

1. OVERVIEW: 

CMS stores the HCRIS cost report files in a relational database.  

The foremost characteristic of this database is the fact that data 
elements will be distributed in flat files aligned with the database table 
in which they reside in our database.  

You will be able to access the entire set of HCRIS Cost Report data that
is submitted to HCRIS by a Fiscal Intermediary on behalf of a provider.  The 
major benefit for all users is the ability to use Relational Database Technology
to quickly exclude certain fields of data or perform cross-sectional analysis.

2. INTRODUCTION:  

The CMS Form 1728-20 HHA Cost Report data files contain cost reports with 
cost reporting periods beginning on or after January 1, 2020, and ending on 
or after December 31, 2020. Prior reports are available in the HHA94 (1728-94) form.
The data files containthe highest level of Medicare cost report status.  If HCRIS has 
both an as submitted report and a final settled report from an HHA for a particular 
year, the data files will only contain the final settled report. If HCRIS has 
an as submitted, final settled, and reopened report from an HHA for a 
particular year, the data files will contain the reopened cost report. It is 
possible for one HHA provider to submit two or more cost reports for a given year
for the same cost report status.  This may happen if a provider changes
its fiscal period, or if there is a change of ownership during the year.  

If you have any questions about this product, please contact the HCRIS 
staff via e-mail at HCRIS@cms.hhs.gov.


3. NOTES:  

The data in the HHA database includes cost reports for free-standing HHAs. 
Hospital-based HHA's are included in the Hospital databases.    

To use the HHA cost report database, you first need to determine the data 
that you are interested in by reviewing the cost report forms and the data 
specifications.  You will need to know the Worksheet ID, line, and column 
from the cost report form.  For example, if you wanted to extract the data 
for "Home Health Agency-Number of Skilled Nursing Visits Title XVIII", you
will need to determine where this information is collected in the report and
use these elements as parameters to pull the data from the HHA_RPT_NMRC table.
The number of Home Health Agency Skilled Nursing Visits Title XVIII is collected
on Worksheet S-3, Part I, Line 1, Column 1 so you would create the following condition:  
     Worksheet Code ='S300000'*
     Line Number ='00100'
     Column Number ='00100'    
 
* Use table 2 of the Provider Reimbursement Manual (PRM) chapter 47 to find the worksheet code.

Many lines on the worksheet forms can be subscripted.  For example, the worksheet form
may show line 6, but it is possible that data relating to that line could be reported
on lines 00600 thru 00699.  Keep that in mind when extracting data for a particular line. 


4. FILES AND CONTENTS:

4.1 HHA Data Files : HHA20_FYXXXX.zip

Compressed files containing 3 text(csv) files with the raw data for the fiscal year XXXX to be loaded into the HHA20_RPT, HHA20_ALPHANMRC and HHA20_NMRC tables. 
	
These files contain data elements that are separated by commas.  

4.2 HHA Report Files : HHA20_REPORTS.zip

HHA20_RECORD_COUNTS.csv - A csv file containing a list of the record counts per fiscal year.    

HHA20_COST_REPORT_STATUS_COUNTS.csv - A csv file containing the counts of cost reports per status and fiscal year.  

HHA20_PRVDR_ID_INFO.csv - A csv file containing one line of identifying data for each HHA provider.

4.3 HHA Documentation Files : HHA20_DOCUMENTATION.ZIP

	HHA20_README.TXT - This readme file.

4.4 HCRIS Documentation Files : HHA20_DOCUMENTATION.ZIP

HCRIS_TABLE_DESCRIPTIONS_AND_SQL.txt - A text file containing the descriptions of the tables, and an ANSI SQL Program (non-Database specific) Containing the DDL scripts to create the tables that comprise the HCRIS HHA20 Database.

HCRIS_DATA_DICTIONARY.csv:  A csv file that contains the meanings of the data elements in the Rpt file, the Alphnmrc file, and the Nmrc file.  

HCRIS_Data_Model.pdf - A .pdf file that contains a diagram of the tables.  The columns are listed in the exact order they appear in the files.  
 
4.4 COST REPORTING INFORMATION
		
The HHA20 cost reporting worksheet forms can be found on the CMS website
On the HCRIS Section page click on the link to the Provider Reimbursement Manual, Part II. 

https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/Paper-Based-Manuals-Items/CMS021935 

Then scroll down to Chapter 47. These forms list and describe all the data fields in the cost report.  

5. SET UP GUIDANCE:  

It is important to note that the datafiles you will be provided are not restricted
for use in one given database platform or even a database management system for that 
matter.  You will likely be able to use your existing tools or utilities to 
access the data, given the ability of those tools to handle files up to the size 
of the largest datafile and files containing data arranged in CSV or Comma 
Separated value format.  

Please be certain to examine the individual datafile and corresponding database
table structure carefully or else you may not achieve valid results or even be
able to access the data. If you choose to use a relational or desktop database
management system, please be mindful of the sizes of the various datafiles.   


6. DISCLAIMER OF WARRANTY:    

The Centers for Medicare & Medicaid Services shall retain no responsibility for 
the data recipients inability to load, examine, or otherwise use the published 
data for the HCRIS system.  

The information in these files is subject to change, and should be reviewed for 
each release.  





	
