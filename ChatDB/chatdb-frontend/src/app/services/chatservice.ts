import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class ChatService {
  private _messages = new BehaviorSubject<{ sender: string, content: string }[]>([]);
  messages = this._messages.asObservable();

  private _isLoading = new BehaviorSubject<boolean>(false);
  isLoading = this._isLoading.asObservable();

  addUserMessage(content: string) {
    this.addMessage({ sender: 'user', content });
    this._isLoading.next(true);

    // Simulate response from ChatDB
    setTimeout(() => {
      this.addMessage({ sender: 'db', content: 'Response from ChatDB' });
      this._isLoading.next(false);
    }, 1000);
  }

  private addMessage(message: { sender: string, content: string }) {
    this._messages.next([...this._messages.value, message]);
  }
}
