import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private baseUrl = 'http://localhost:5004'; // Flask backend base URL
  private messagesSubject = new BehaviorSubject<{ sender: string, content: string }[]>([]);
  private isLoadingSubject = new BehaviorSubject<boolean>(false);

  messages$ = this.messagesSubject.asObservable();
  isLoading$ = this.isLoadingSubject.asObservable();

  constructor(private http: HttpClient) {}

  sendMessageToSQL(query: any): void {
    this.isLoadingSubject.next(true); // Show the loading spinner
  
    this.http.post(`${this.baseUrl}/query/mysql`, query).subscribe(
      (response) => {
        //console.log('Response from backend (SQL):', response); // Debug log
        this.addMessage({
          sender: 'db',
          content: JSON.stringify(response, null, 2) // Format response for readability
        });
        this.isLoadingSubject.next(false); // Hide the loading spinner
      },
      (error) => {
        //console.error('Error sending SQL query to backend:', error); // Debug log
        this.addMessage({
          sender: 'db',
          content: `Error: ${error.message}`
        });
        this.isLoadingSubject.next(false); // Hide the loading spinner
      }
    );
  }
  
  sendMessageToMongoDB(query: any): void {
    this.isLoadingSubject.next(true); // Show the loading spinner
    this.http.post(`${this.baseUrl}/query/mongodb`, query).subscribe(
      (response) => {
        console.log('Response from backend:', response); // Debug log
        this.addMessage({
          sender: 'db',
          content: JSON.stringify(response, null, 2) // Format response for readability
        });
        this.isLoadingSubject.next(false); // Hide the loading spinner
      },
      (error) => {
        console.error('Error sending message to MongoDB:', error); // Debug log
        this.addMessage({
          sender: 'db',
          content: `Error: ${error.message}`
        });
        this.isLoadingSubject.next(false); // Hide the loading spinner
      }
    );
  }

  fetchMongoDBMetadata(): Observable<any> {
    console.log('Sending request to fetch MongoDB metadata...');
    return this.http.get(`${this.baseUrl}/metadata/mongodb`);
  }
  

  public addMessage(message: { sender: string, content: string }): void {
    const currentMessages = this.messagesSubject.value;
    this.messagesSubject.next([...currentMessages, message]);
  }
}

