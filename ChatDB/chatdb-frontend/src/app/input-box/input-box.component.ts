import { Component, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-input-box',
  templateUrl: './input-box.component.html',
  styleUrls: ['./input-box.component.css']
})
export class InputBoxComponent {
  query: string = '';
  @Output() sendMessage = new EventEmitter<string>();

  submitQuery() {
    if (this.query.trim()) {
      this.sendMessage.emit(this.query);
      this.query = '';
    }
  }
}
