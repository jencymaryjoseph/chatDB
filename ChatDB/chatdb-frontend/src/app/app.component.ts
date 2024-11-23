import { Component } from '@angular/core';
import { ChatService } from './services/chatservice';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'ChatDB';
  
  public chatService: ChatService; // Ensure chatService is public

  constructor(chatService: ChatService) {
    this.chatService = chatService;
  }

  public fetchMetadata() {
    console.log('Fetch Metadata button clicked'); // Add debug log
    this.chatService.fetchMongoDBMetadata().subscribe(
      (metadata) => {
        console.log('Metadata received:', metadata); // Debug log
        this.chatService.addMessage({
          sender: 'db',
          content: JSON.stringify(metadata)
        });
      },
      (error) => {
        console.error('Error fetching metadata:', error); // Debug log
      }
    );
  }
  

  handleUserMessage(message: string) {
    // Immediately display the user's message in the chat window
    this.chatService.addMessage({
      sender: 'user',
      content: message
    });
  
    let query;
    try {
      // Parse the full query as JSON
      query = JSON.parse(message);
      console.log('Parsed query:', query); // Debug log
  
      // Validate query structure
      if (!query.collection || !query.filter) {
        throw new Error('Invalid query structure: "collection" and "filter" fields are required.');
      }
    } catch (error) {
      console.error('Invalid query format:', error);
      this.chatService.addMessage({
        sender: 'db',
        content: 'Error: Invalid query format. Ensure the JSON contains "collection" and "filter".'
      });
      return;
    }
  
    console.log('Sending query to backend:', query); // Debug log
    this.chatService.sendMessageToMongoDB(query);
  }
}


// import { Component } from '@angular/core';
// import { RouterOutlet } from '@angular/router';
// import { ChatService } from './services/chatservice';

// @Component({
//   selector: 'app-root',
//   // standalone: true,
//   // imports: [RouterOutlet],
//   templateUrl: './app.component.html',
//   styleUrl: './app.component.css'
// })
// export class AppComponent {
//   constructor(private chatService: ChatService) {}

//   handleUserMessage(message: string) {
//     this.chatService.addUserMessage(message);
//   }
// }
