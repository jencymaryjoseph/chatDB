import { Component, OnInit } from '@angular/core';
import { ChatService } from '../services/chatservice';

@Component({
  selector: 'app-chat-window',
  templateUrl: './chat-window.component.html',
  styleUrls: ['./chat-window.component.css']
})
export class ChatWindowComponent implements OnInit {
  messages = this.chatService.messages;
  isLoading = this.chatService.isLoading;

  constructor(private chatService: ChatService) {}

  ngOnInit(): void {}
}
