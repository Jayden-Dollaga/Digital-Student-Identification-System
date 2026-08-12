# Digital Student Identification System for Improved Student Identification and Attendance Monitoring

## Introduction / Background

Student identification is an important part of school life. Schools need to know who is present, who is absent, and who is entering a school office or facility. In many schools, this is still done manually through attendance sheets, roll calls, or visual checking. These methods may seem simple, but they can also cause delays, mistakes, and confusion, especially in large classes or busy school environments.

Manual identification can be time-consuming and may lead to errors such as missing names, duplicate entries, or false attendance records. In some cases, students may be marked present even when they are not physically present, or a student may be identified by another person instead of their own identity. These problems can affect the accuracy of school records and make attendance monitoring less efficient.

Because of this, schools need a faster and more reliable way to identify students and record attendance. Digital identification can help solve this problem by making the process more systematic and organized. One useful technology for this purpose is biometric identification, especially fingerprint recognition. A fingerprint is unique to a person, so it can be used as a reliable method of identity verification.

The Digital Student Identification System (DSIS) is a practical project that applies this idea to school settings. The project explores how a fingerprint-based system can help identify registered students and record attendance-related information in a digital format. In this repository, the DSIS prototype is designed around an ESP32 microcontroller, an AS608 fingerprint sensor, a Python-based desktop application, and a local database. This makes the project relevant to the CSS/TVL-ICT strand because it combines hardware, software, database management, and system design in one real-world solution.

## Statement of the Problem

The main problem that DSIS aims to address is the difficulty of maintaining accurate and efficient student identification and attendance monitoring in schools.

Many schools still rely on traditional methods of attendance recording. These methods usually require teachers to check names one by one, which takes time and may create errors. A student may be late, a teacher may forget to record attendance, or a record may be entered incorrectly. Because of these problems, the process becomes less organized and less reliable.

Another concern is the need for a secure and dependable way to verify a student’s identity. In some cases, manual systems can allow mistakes in identification, especially when many students are involved. This is where a digital system can help by providing a more structured and modern method of identification.

This leads to the following questions: How can schools improve the accuracy of student identification? How can attendance records be organized more efficiently? How can the process become easier for both teachers and students? The DSIS concept responds to these issues by proposing a fingerprint-based identification system that can support digital attendance monitoring.

## Proposed Project or Solution

The proposed solution is the Digital Student Identification System (DSIS), a project designed to improve student identification and attendance processes using fingerprint recognition. The system is intended to work by capturing a student’s fingerprint through a fingerprint sensor and comparing it with previously enrolled fingerprints. Once the fingerprint is recognized, the system can identify the student and record the attendance-related data in a digital database.

The prototype in this repository uses an ESP32 microcontroller connected to an AS608 fingerprint sensor. The sensor collects the fingerprint data, and the microcontroller handles communication between the hardware and the computer application. The software part of the project is designed to receive the identification result, process the data, and store attendance-related information using a local database. The system also includes a GUI that allows users to manage records, monitor activity, and review attendance information.

Because the system uses fingerprint data, it should be managed responsibly. Access to student biometric information must be limited to authorized users, and records should be protected to maintain privacy and trust. This is important because biometric information is sensitive and should not be treated casually.

This means the project does not only focus on identification alone. It also supports attendance monitoring by organizing student records and system logs in a more convenient digital form. The idea behind DSIS is to provide a practical and affordable solution that can help schools manage student attendance in a more efficient way.

## Objectives

### General Objective

To propose a digital student identification system that can help improve the efficiency and organization of student identification and attendance monitoring.

### Specific Objectives

1. To provide a digital method of identifying registered students.
2. To use fingerprint verification as a practical means of student identification.
3. To reduce the dependence on manual attendance recording.
4. To organize student and attendance-related information in a digital database.
5. To provide a user-friendly interface for monitoring system activity.
6. To create a prototype that demonstrates the application of ICT skills in solving a school-related problem.

## Benefits of the Project

The DSIS project can provide several benefits to the school community. First, it can make student identification faster and more organized than manual checking. Students can simply place their finger on the sensor, and the system can identify them with minimal delay. This can help reduce time spent during attendance taking.

Second, the project can help teachers and school personnel by improving how attendance records are stored and managed. Instead of relying only on paper records, the system can maintain digital information that is easier to review and organize. This can reduce the risk of lost or damaged attendance sheets.

Third, the project may help improve the accuracy of school attendance tracking. Because fingerprint data is unique to each person, the system can support a more reliable identification process compared with manual or visual checking. Although no system is perfect, it can still reduce common errors in the attendance process.

The project also has educational value. For CSS/TVL-ICT students, DSIS is a useful example of how hardware and software can be combined to solve a real problem. It develops practical skills in system design, programming, electronics, database management, and application development.

## Target Beneficiaries

The primary beneficiaries of DSIS are the students, because they are directly involved in the identification process. With a digital system, student attendance can be recorded more quickly and clearly.

Teachers are also important beneficiaries. They can spend less time manually checking attendance and more time focusing on teaching and classroom instruction. The system may also help them monitor attendance records more effectively.

School personnel and administrators can benefit from having organized and accessible student information. A digital identification system can support better record management and improve the overall flow of school operations.

Finally, CSS/TVL-ICT students and the school community can benefit from the project as an example of practical technology use. It shows how modern ICT tools can be applied to solve everyday school problems.

## Conclusion

The Digital Student Identification System is a practical concept designed to address common problems in student identification and attendance monitoring. Many schools still depend on manual methods that are time-consuming and prone to mistakes. DSIS offers a more organized and modern solution by using fingerprint-based identification and digital record management.

Although the project is still a prototype and not a fully deployed school system, it shows how technology can help improve school processes in a realistic way. It can support students, teachers, and school staff by making identification faster, more accurate, and more efficient. In this way, DSIS can contribute to the improvement of student identification and attendance-related processes while also showing the value of ICT in everyday school life.

## References

Jain, A. K., Ross, A., & Prabhakar, S. (2004). An introduction to biometric recognition. IEEE Transactions on Circuits and Systems for Video Technology, 14(1), 4–20.

Maltoni, D., Maio, D., Jain, A. K., & Prabhakar, S. (2009). Handbook of fingerprint recognition. Springer.

International Organization for Standardization. (2011). Information technology — Biometric data interchange formats — Part 2: Finger minutiae data (ISO/IEC 19794-2). Geneva, Switzerland: ISO.
